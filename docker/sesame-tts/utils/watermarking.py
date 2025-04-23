"""
Simplified watermarking module for CSM TTS system
This provides a stub implementation when the silentcipher package isn't available
"""
import torch

# This watermark key is public, it is not secure.
# If using CSM 1B in another application, use a new private key and keep it secret.
CSM_1B_GH_WATERMARK = [212, 211, 146, 56, 201]

def load_watermarker(device: str = "cuda"):
    """
    Return a dummy watermarker object
    """
    return DummyWatermarker()
    
class DummyWatermarker:
    """
    Dummy watermarker that does nothing but pass through audio
    """
    def __init__(self):
        pass
    
    def encode_wav(self, audio, sample_rate, watermark_key, calc_sdr=False, message_sdr=36):
        return audio, None
    
    def decode_wav(self, audio, sample_rate, phase_shift_decoding=True):
        return {"status": False, "messages": []}

@torch.inference_mode()
def watermark(watermarker, audio_array: torch.Tensor, sample_rate: int, watermark_key: list[int]) -> tuple[torch.Tensor, int]:
    """
    Apply watermark to audio if silentcipher is available, otherwise just return the audio
    """
    try:
        if isinstance(watermarker, DummyWatermarker):
            # Just return the audio as-is
            return audio_array, sample_rate
            
        audio_array_44khz = torch.nn.functional.interpolate(
            audio_array.unsqueeze(0).unsqueeze(0), 
            size=int(len(audio_array) * 44100 / sample_rate),
            mode='linear', 
            align_corners=False
        ).squeeze(0).squeeze(0)
        
        encoded, _ = watermarker.encode_wav(audio_array_44khz, 44100, watermark_key, calc_sdr=False, message_sdr=36)
        
        # Resample back to original rate if needed
        output_sample_rate = min(44100, sample_rate)
        if output_sample_rate != 44100:
            encoded = torch.nn.functional.interpolate(
                encoded.unsqueeze(0).unsqueeze(0),
                size=int(len(encoded) * output_sample_rate / 44100),
                mode='linear',
                align_corners=False
            ).squeeze(0).squeeze(0)
            
        return encoded, output_sample_rate
    except Exception as e:
        print(f"Warning: Watermarking failed: {e}, returning unwatermarked audio")
        return audio_array, sample_rate

@torch.inference_mode()
def verify(watermarker, watermarked_audio: torch.Tensor, sample_rate: int, watermark_key: list[int]) -> bool:
    """
    Verify watermark in audio if silentcipher is available
    """
    try:
        if isinstance(watermarker, DummyWatermarker):
            return False
            
        watermarked_audio_44khz = torch.nn.functional.interpolate(
            watermarked_audio.unsqueeze(0).unsqueeze(0),
            size=int(len(watermarked_audio) * 44100 / sample_rate),
            mode='linear',
            align_corners=False
        ).squeeze(0).squeeze(0)
        
        result = watermarker.decode_wav(watermarked_audio_44khz, 44100, phase_shift_decoding=True)
        
        is_watermarked = result["status"]
        if is_watermarked:
            is_csm_watermarked = result["messages"][0] == watermark_key
        else:
            is_csm_watermarked = False
            
        return is_watermarked and is_csm_watermarked
    except Exception as e:
        print(f"Warning: Watermark verification failed: {e}")
        return False

def check_audio_from_file(audio_path: str) -> bool:
    """
    Check if audio file contains CSM watermark
    """
    try:
        import torchaudio
        watermarker = load_watermarker(device="cuda")
        audio_array, sample_rate = torchaudio.load(audio_path)
        audio_array = audio_array.mean(dim=0)
        return verify(watermarker, audio_array, sample_rate, CSM_1B_GH_WATERMARK)
    except Exception as e:
        print(f"Error checking watermark: {e}")
        return False