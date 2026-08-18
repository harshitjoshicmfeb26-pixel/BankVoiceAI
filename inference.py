import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
import torchvision.models as models
from PIL import Image
import onnxruntime as ort
from huggingface_hub import hf_hub_download

# ==========================================
# CẤU HÌNH REPO
# ==========================================
REPO_ID = "biometric-ai-lab/Face_Recognition"
RECOG_FILENAME = "pytorch_model.bin"
YOLO_FILENAME = "yolov8s-face-lindevs.onnx"


# ==========================================
# 1. MODEL ARCHITECTURE
# ==========================================
class FaceRecognitionModel(nn.Module):
    def __init__(self):
        super(FaceRecognitionModel, self).__init__()
        self.backbone = models.wide_resnet101_2(weights=None)
        self.backbone.fc = nn.Identity()
        self.embed = nn.Sequential(
            nn.Linear(2048, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
        )

    def forward(self, img):
        features = self.backbone(img)
        embedding = self.embed(features)
        return F.normalize(embedding, p=2, dim=1)


# ==========================================
# 2. YOLO DETECTOR
# ==========================================
class YOLOFaceDetector:
    def __init__(self, model_path, conf_threshold=0.5):
        # Force CPU provider for maximum compatibility on local runs
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]
        self.conf_threshold = conf_threshold
        self.input_size = 640

    def detect_extract_face(self, image_pil, expand_ratio=0.0):
        image_np = np.array(image_pil)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        img_height, img_width = image_bgr.shape[:2]

        img_resized = cv2.resize(image_bgr, (self.input_size, self.input_size))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        img_batch = np.expand_dims(img_transposed, axis=0)

        outputs = self.session.run(self.output_names, {self.input_name: img_batch})
        predictions = outputs[0]

        if len(predictions.shape) == 3:
            predictions = predictions[0].T

        best_face = None
        max_area = 0

        for pred in predictions:
            conf = pred[4]
            if conf > self.conf_threshold:
                x_center, y_center, w, h = pred[:4]

                x_center = x_center * img_width / self.input_size
                y_center = y_center * img_height / self.input_size
                w = w * img_width / self.input_size
                h = h * img_height / self.input_size

                x1 = int(x_center - w / 2)
                y1 = int(y_center - h / 2)
                x2 = int(x_center + w / 2)
                y2 = int(y_center + h / 2)

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(img_width, x2)
                y2 = min(img_height, y2)

                area = (x2 - x1) * (y2 - y1)

                if area > max_area:
                    max_area = area
                    best_face = (x1, y1, x2, y2)

        if best_face:
            x1, y1, x2, y2 = best_face

            if expand_ratio != 0:
                w_box = x2 - x1
                h_box = y2 - y1
                pad = int(expand_ratio * max(w_box, h_box))
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(img_width, x2 + pad)
                y2 = min(img_height, y2 + pad)

            return image_pil.crop((x1, y1, x2, y2))

        print("Warning: No face detected. Using full image.")
        return image_pil


# ==========================================
# 3. FACE ANALYSIS WRAPPER
# ==========================================
class FaceAnalysis:
    def __init__(self, device=None):
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Initializing Face Analysis on {self.device}...")

        try:
            print(f"Checking models from {REPO_ID}...")
            recog_path = hf_hub_download(repo_id=REPO_ID, filename=RECOG_FILENAME)
            yolo_path = hf_hub_download(repo_id=REPO_ID, filename=YOLO_FILENAME)
        except Exception as e:
            raise RuntimeError(f"Failed to download models from Hugging Face Hub.\nError: {e}")

        self.yolo = YOLOFaceDetector(yolo_path, conf_threshold=0.5)
        self.model = FaceRecognitionModel().to(self.device)

        checkpoint = torch.load(recog_path, map_location=self.device)
        if 'model' in checkpoint:
            self.model.load_state_dict(checkpoint['model'])
        elif 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)

        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
        print("Face Recognition Local Model Loaded successfully!")

    def process_image(self, image_source, expand_ratio=0.0):
        if isinstance(image_source, str):
            if not os.path.exists(image_source):
                raise FileNotFoundError(f"Image not found: {image_source}")
            img_pil = Image.open(image_source).convert('RGB')
        elif isinstance(image_source, Image.Image):
            img_pil = image_source.convert('RGB')
        elif isinstance(image_source, np.ndarray):
            img_pil = Image.fromarray(cv2.cvtColor(image_source, cv2.COLOR_BGR2RGB))
        else:
            raise ValueError("Input must be filepath, PIL Image, or Numpy Array")

        face_crop = self.yolo.detect_extract_face(img_pil, expand_ratio=expand_ratio)
        img_tensor = self.transform(face_crop).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model(img_tensor)

        return embedding

    def compare(self, img1, img2, threshold=0.45, expand_ratio=0.01):
        emb1 = self.process_image(img1, expand_ratio)
        emb2 = self.process_image(img2, expand_ratio)

        similarity = F.cosine_similarity(emb1, emb2).item()
        is_same = similarity > threshold

        return similarity, is_same
