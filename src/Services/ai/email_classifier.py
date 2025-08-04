import torch
import json
import sys
import os
import numpy as np
from transformers import AutoTokenizer

class EmailClassifier:
    def __init__(self, model_path=None):
        try:
            if model_path is None:
                # Construct absolute path from script location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
                model_path = os.path.join(project_root, 'models', 'email_classifier')
                print(f"Looking for model at: {model_path}", file=sys.stderr)
            
            if not os.path.exists(model_path):
                raise ValueError(f"Model directory not found: {model_path}")
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load tokenizer with trust_remote_code for local files
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,
                trust_remote_code=True)
            
            # Try ONNX model first, then fallback to PyTorch
            try:
                import onnxruntime as ort
                onnx_model_path = os.path.join(model_path, "model.onnx")
                if os.path.exists(onnx_model_path):
                    self.session = ort.InferenceSession(onnx_model_path)
                    self.is_onnx = True
                else:
                    # Fallback to PyTorch model
                    from transformers import AutoModelForSequenceClassification
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        model_path,
                        local_files_only=True,
                        trust_remote_code=True
                    ).to(self.device)
                    self.is_onnx = False
            except ImportError:
                # ONNX not available, use PyTorch
                from transformers import AutoModelForSequenceClassification
                self.model = AutoModelForSequenceClassification.from_pretrained(
                        model_path,
                        local_files_only=True,
                        trust_remote_code=True
                    ).to(self.device)
                self.is_onnx = False
            
            self.labels = {
                0: "Interested",
                1: "Meeting Booked",
                2: "Not Interested",
                3: "Spam",
                4: "Out of Office"
            }
            self.initialized = True
        except Exception as e:
            self.initialized = False
            self.error = str(e)

    def predict(self, email_text):
        if not self.initialized:
            return {"category": "Unclassified", "error": self.error}
        
        try:
            inputs = self.tokenizer(
                email_text,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt" if not self.is_onnx else "np"
            )
            
            if self.is_onnx:
                # ONNX inference
                if isinstance(inputs['input_ids'], torch.Tensor):
                    input_ids = inputs['input_ids'].numpy()
                    attention_mask = inputs['attention_mask'].numpy()
                else:
                    input_ids = inputs['input_ids']
                    attention_mask = inputs['attention_mask']
                    
                onnx_inputs = {
                    'input_ids': input_ids.astype(np.int64),
                    'attention_mask': attention_mask.astype(np.int64)
                }
                outputs = self.session.run(None, onnx_inputs)
                logits = torch.tensor(outputs[0])
            else:
                # PyTorch inference
                inputs = inputs.to(self.device)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                logits = outputs.logits
            
            probs = torch.nn.functional.softmax(logits, dim=-1)
            predicted_id = int(torch.argmax(probs).item())
            confidence = torch.max(probs).item()
            
            return {
                "category": self.labels[predicted_id],
                "confidence": float(confidence)
            }
        except Exception as e:
            return {"category": "Unclassified", "error": str(e)}

def main():
    try:
        # Handle test mode
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            classifier = EmailClassifier()
            if classifier.initialized:
                print(json.dumps({
                    "category": "Test",
                    "status": "available",
                    "confidence": 1.0
                }), flush=True)
            else:
                print(json.dumps({
                    "category": "Unclassified",
                    "error": classifier.error
                }), flush=True)
            return

        # Read email text from stdin
        email_text = sys.stdin.read().strip()
        
        if not email_text:
            print(json.dumps({"category": "Unclassified", "error": "No input provided"}))
            return

        # Initialize classifier and predict
        classifier = EmailClassifier()
        result = classifier.predict(email_text)
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"category": "Unclassified", "error": str(e)}))

if __name__ == "__main__":
    main()