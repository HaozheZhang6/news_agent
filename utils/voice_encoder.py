#!/usr/bin/env python3
"""
Voice Samples Encoder Utility with Modern Audio Compression

This utility compresses voice sample files using modern codecs (Opus, AAC) 
before encoding to base64 format suitable for WebSocket transmission.
Preserves original files while creating compressed versions.

Usage:
    python voice_encoder.py [input_file] [output_file]
    python voice_encoder.py --batch [directory]
    python voice_encoder.py --test [file]
    python voice_encoder.py --compress [file] --codec opus
"""

import os
import sys
import base64
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import uuid
from datetime import datetime


class VoiceEncoder:
    """Encodes voice samples to WebSocket-compatible format with modern compression"""
    
    def __init__(self):
        self.demo_user_id = "03f6b167-0c4d-4983-a380-54b8eb42f830"
        self.supported_formats = {'.wav', '.webm', '.mp3', '.m4a', '.ogg', '.flac'}
        
        # Modern compression codecs and their settings
        self.compression_codecs = {
            'opus': {
                'extension': '.opus',
                'codec': 'libopus',  # Use libopus instead of opus
                'bitrate': '64k',  # Optimal for speech
                'sample_rate': '16000',
                'channels': '1',
                'description': 'Opus - Best for real-time speech (WebRTC standard)'
            },
            'aac': {
                'extension': '.m4a',
                'codec': 'aac',
                'bitrate': '128k',  # Good quality/size balance
                'sample_rate': '16000',
                'channels': '1',
                'description': 'AAC - High quality compression'
            },
            'mp3': {
                'extension': '.mp3',
                'codec': 'libmp3lame',
                'bitrate': '128k',
                'sample_rate': '16000',
                'channels': '1',
                'description': 'MP3 - Widely supported'
            },
            'webm': {
                'extension': '.webm',
                'codec': 'libopus',
                'bitrate': '64k',
                'sample_rate': '16000',
                'channels': '1',
                'description': 'WebM - Web optimized'
            }
        }
    
    def compress_audio(self, input_path: str, codec: str = 'opus') -> Tuple[str, Dict[str, Any]]:
        """
        Compress audio file using modern codecs
        
        Args:
            input_path: Path to input audio file
            codec: Compression codec (opus, aac, mp3, webm)
            
        Returns:
            Tuple of (compressed_file_path, compression_info)
        """
        if codec not in self.compression_codecs:
            raise ValueError(f"Unsupported codec: {codec}. Supported: {list(self.compression_codecs.keys())}")
        
        input_file = Path(input_path)
        codec_config = self.compression_codecs[codec]
        
        # Create temporary file for compressed output
        temp_dir = Path(tempfile.gettempdir()) / "voice_encoder"
        temp_dir.mkdir(exist_ok=True)
        
        compressed_file = temp_dir / f"{input_file.stem}_compressed{codec_config['extension']}"
        
        # FFmpeg command for compression
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', str(input_file),
            '-c:a', codec_config['codec'],  # Use the actual codec name
            '-b:a', codec_config['bitrate'],
            '-ar', codec_config['sample_rate'],
            '-ac', codec_config['channels'],
            '-y',  # Overwrite output file
            str(compressed_file)
        ]
        
        try:
            # Run FFmpeg compression
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
            
            # Get compression info
            original_size = input_file.stat().st_size
            compressed_size = compressed_file.stat().st_size
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 1
            
            compression_info = {
                'codec': codec,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'bitrate': codec_config['bitrate'],
                'sample_rate': codec_config['sample_rate'],
                'description': codec_config['description']
            }
            
            return str(compressed_file), compression_info
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg compression failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg to use compression features.")

    def encode_file(self, input_path: str, output_path: Optional[str] = None, 
                   compress: bool = True, codec: str = 'opus') -> Dict[str, Any]:
        """
        Encode a single audio file to base64 with optional compression
        
        Args:
            input_path: Path to input audio file
            output_path: Optional path for output JSON file
            compress: Whether to compress audio before encoding
            codec: Compression codec to use
            
        Returns:
            Dictionary containing WebSocket message format
        """
        input_file = Path(input_path)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if input_file.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported format: {input_file.suffix}. Supported: {self.supported_formats}")
        
        # Compress audio if requested
        audio_file_path = input_path
        compression_info = None
        
        if compress:
            try:
                audio_file_path, compression_info = self.compress_audio(input_path, codec)
                print(f"🎵 Compressed with {codec.upper()}: {compression_info['compression_ratio']:.1f}x smaller")
            except Exception as e:
                print(f"⚠️ Compression failed, using original: {e}")
                audio_file_path = input_path
        
        # Read and encode audio file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        # Determine format - use compressed format if compression was applied
        if compress and compression_info:
            audio_format = self._get_format(Path(audio_file_path).suffix)
        else:
            audio_format = self._get_format(input_file.suffix)
        
        # Create WebSocket message
        session_id = str(uuid.uuid4())
        message = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": base64_audio,
                "format": audio_format,
                "is_final": True,
                "session_id": session_id,
                "user_id": self.demo_user_id,
                "sample_rate": self._get_sample_rate(audio_format),
                "file_size": len(audio_data),
                "original_filename": input_file.name,
                "encoded_at": datetime.now().isoformat(),
                "compression": compression_info
            }
        }
        
        # Save to output file if specified
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(message, f, indent=2)
            
            print(f"✅ Encoded: {input_file.name} -> {output_file.name}")
            print(f"   Size: {len(audio_data):,} bytes -> {len(base64_audio):,} chars")
            print(f"   Session ID: {session_id}")
        
        # Clean up temporary compressed file
        if compress and audio_file_path != input_path:
            try:
                Path(audio_file_path).unlink()
            except:
                pass
        
        return message
    
    def encode_batch(self, input_dir: str, output_dir: Optional[str] = None, 
                    compress: bool = True, codec: str = 'opus') -> Dict[str, Any]:
        """
        Encode all audio files in a directory with compression
        
        Args:
            input_dir: Directory containing audio files
            output_dir: Optional output directory for encoded files
            compress: Whether to compress audio before encoding
            codec: Compression codec to use
            
        Returns:
            Summary of encoding results
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            suffix = f"_compressed_{codec}" if compress else "_encoded"
            output_path = input_path / f"encoded{suffix}"
            output_path.mkdir(exist_ok=True)
        
        results = {
            "successful": [],
            "failed": [],
            "skipped": [],
            "compression_stats": {
                "total_original_size": 0,
                "total_compressed_size": 0,
                "average_compression_ratio": 0
            }
        }
        
        # Find all audio files
        audio_files = []
        for ext in self.supported_formats:
            audio_files.extend(input_path.glob(f"*{ext}"))
            audio_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        print(f"🔍 Found {len(audio_files)} audio files in {input_dir}")
        if compress:
            print(f"🎵 Compression: {codec.upper()} enabled")
        
        for audio_file in audio_files:
            try:
                suffix = f"_compressed_{codec}" if compress else "_encoded"
                output_file = output_path / f"{audio_file.stem}{suffix}.json"
                message = self.encode_file(str(audio_file), str(output_file), compress, codec)
                
                results["successful"].append(audio_file.name)
                
                # Track compression stats
                if compress and message["data"].get("compression"):
                    comp_info = message["data"]["compression"]
                    results["compression_stats"]["total_original_size"] += comp_info["original_size"]
                    results["compression_stats"]["total_compressed_size"] += comp_info["compressed_size"]
                
            except Exception as e:
                print(f"❌ Failed to encode {audio_file.name}: {e}")
                results["failed"].append({"file": audio_file.name, "error": str(e)})
        
        # Calculate average compression ratio
        if results["compression_stats"]["total_compressed_size"] > 0:
            results["compression_stats"]["average_compression_ratio"] = (
                results["compression_stats"]["total_original_size"] / 
                results["compression_stats"]["total_compressed_size"]
            )
        
        return results
    
    def test_encoding(self, input_path: str, compress: bool = True, codec: str = 'opus') -> Dict[str, Any]:
        """
        Test encoding without saving output file
        
        Args:
            input_path: Path to input audio file
            compress: Whether to test compression
            codec: Compression codec to test
            
        Returns:
            Encoding test results
        """
        try:
            message = self.encode_file(input_path, compress=compress, codec=codec)
            
            # Calculate compression ratio
            original_size = message["data"]["file_size"]
            encoded_size = len(message["data"]["audio_chunk"])
            compression_ratio = encoded_size / original_size
            
            result = {
                "success": True,
                "original_size": original_size,
                "encoded_size": encoded_size,
                "compression_ratio": compression_ratio,
                "format": message["data"]["format"],
                "session_id": message["data"]["session_id"]
            }
            
            # Add compression info if available
            if message["data"].get("compression"):
                comp_info = message["data"]["compression"]
                result["compression"] = comp_info
                result["audio_compression_ratio"] = comp_info["compression_ratio"]
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_format(self, extension: str) -> str:
        """Map file extension to WebSocket format"""
        format_map = {
            '.wav': 'wav',
            '.webm': 'webm',
            '.mp3': 'mp3',
            '.m4a': 'm4a',
            '.ogg': 'ogg',
            '.opus': 'opus',  # Add Opus support
            '.flac': 'flac'
        }
        return format_map.get(extension.lower(), 'wav')
    
    def _get_sample_rate(self, format: str) -> int:
        """Get default sample rate for format"""
        sample_rates = {
            'wav': 16000,
            'webm': 48000,
            'mp3': 44100,
            'm4a': 44100,
            'ogg': 48000,
            'opus': 16000,  # Opus typically uses 16kHz for speech
            'flac': 44100
        }
        return sample_rates.get(format, 16000)


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Encode voice samples for WebSocket transmission with modern compression")
    parser.add_argument("input", nargs="?", help="Input audio file or directory")
    parser.add_argument("-o", "--output", help="Output file or directory")
    parser.add_argument("--batch", action="store_true", help="Batch encode all files in directory")
    parser.add_argument("--test", action="store_true", help="Test encoding without saving")
    parser.add_argument("--compress", action="store_true", default=True, help="Enable audio compression (default: True)")
    parser.add_argument("--no-compress", action="store_true", help="Disable audio compression")
    parser.add_argument("--codec", choices=['opus', 'aac', 'mp3', 'webm'], default='opus', 
                       help="Compression codec (default: opus)")
    parser.add_argument("--demo-user-id", default="03f6b167-0c4d-4983-a380-54b8eb42f830", 
                       help="Demo user ID for WebSocket messages")
    
    args = parser.parse_args()
    
    encoder = VoiceEncoder()
    encoder.demo_user_id = args.demo_user_id
    
    # Determine compression settings
    compress = args.compress and not args.no_compress
    
    try:
        if args.test and args.input:
            # Test mode
            print(f"🧪 Testing encoding: {args.input}")
            if compress:
                print(f"🎵 Compression: {args.codec.upper()} enabled")
            else:
                print("📦 Compression: disabled")
                
            result = encoder.test_encoding(args.input, compress, args.codec)
            
            if result["success"]:
                print(f"✅ Test successful!")
                print(f"   Original size: {result['original_size']:,} bytes")
                print(f"   Encoded size: {result['encoded_size']:,} chars")
                print(f"   Base64 ratio: {result['compression_ratio']:.2f}x")
                
                if result.get("compression"):
                    comp_info = result["compression"]
                    print(f"   Audio compression: {comp_info['compression_ratio']:.1f}x smaller")
                    print(f"   Codec: {comp_info['codec'].upper()} @ {comp_info['bitrate']}")
                    print(f"   Sample rate: {comp_info['sample_rate']} Hz")
                
                print(f"   Format: {result['format']}")
                print(f"   Session ID: {result['session_id']}")
            else:
                print(f"❌ Test failed: {result['error']}")
                sys.exit(1)
        
        elif args.batch and args.input:
            # Batch mode
            print(f"📦 Batch encoding directory: {args.input}")
            if compress:
                print(f"🎵 Compression: {args.codec.upper()} enabled")
            else:
                print("📦 Compression: disabled")
                
            results = encoder.encode_batch(args.input, args.output, compress, args.codec)
            
            print(f"\n📊 Batch encoding complete:")
            print(f"   ✅ Successful: {len(results['successful'])}")
            print(f"   ❌ Failed: {len(results['failed'])}")
            print(f"   ⏭️ Skipped: {len(results['skipped'])}")
            
            if compress and results["compression_stats"]["average_compression_ratio"] > 0:
                stats = results["compression_stats"]
                print(f"\n🎵 Compression statistics:")
                print(f"   Total original size: {stats['total_original_size']:,} bytes")
                print(f"   Total compressed size: {stats['total_compressed_size']:,} bytes")
                print(f"   Average compression ratio: {stats['average_compression_ratio']:.1f}x")
                print(f"   Space saved: {((stats['total_original_size'] - stats['total_compressed_size']) / stats['total_original_size'] * 100):.1f}%")
            
            if results["failed"]:
                print("\n❌ Failed files:")
                for failure in results["failed"]:
                    print(f"   - {failure['file']}: {failure['error']}")
        
        elif args.input:
            # Single file mode
            print(f"🎵 Encoding single file: {args.input}")
            if compress:
                print(f"🎵 Compression: {args.codec.upper()} enabled")
            else:
                print("📦 Compression: disabled")
                
            message = encoder.encode_file(args.input, args.output, compress, args.codec)
            print(f"✅ Encoding complete!")
            print(f"   Session ID: {message['data']['session_id']}")
            print(f"   Format: {message['data']['format']}")
            print(f"   Size: {message['data']['file_size']:,} bytes")
            
            if message['data'].get('compression'):
                comp_info = message['data']['compression']
                print(f"   Compression: {comp_info['compression_ratio']:.1f}x smaller with {comp_info['codec'].upper()}")
        
        else:
            # Interactive mode
            print("🎤 Voice Samples Encoder with Modern Compression")
            print("=" * 60)
            print("Usage examples:")
            print("  python voice_encoder.py audio.wav")
            print("  python voice_encoder.py audio.wav -o encoded.json")
            print("  python voice_encoder.py --batch ./voice_samples/")
            print("  python voice_encoder.py --test audio.wav")
            print("  python voice_encoder.py --test audio.wav --codec aac")
            print("  python voice_encoder.py --batch ./voice_samples/ --no-compress")
            print("\nSupported formats:", ", ".join(encoder.supported_formats))
            print("\nCompression codecs:")
            for codec, config in encoder.compression_codecs.items():
                print(f"  {codec}: {config['description']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
