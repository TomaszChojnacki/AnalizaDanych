
import sys
import torch

print("=== ANALIZA DANYCH - TEST SRODOWISKA ===")
print("Interpreter:", sys.executable)
print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

print("Srodowisko gotowe!")
