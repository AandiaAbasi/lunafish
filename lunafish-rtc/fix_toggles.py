import re

file_path = '/Users/artinpanahi/projects/video-call/reactnative-application/ios/rateme/NativeCall/Services/NativeCallManager.swift'

with open(file_path, 'r') as f:
    content = f.read()

pattern = r'func toggleMute\(\) -> Bool \{ return false \}[\s\S]*?func switchCamera\(\) \{\}[\s\S]*?agoraService\.switchCamera\(\)\s*\}'
replacement = """func toggleMute() -> Bool { return false }
    func toggleSpeaker() -> Bool { return false }
    func toggleVideo() -> Bool { return false }
    func switchCamera() {}"""

content = re.sub(pattern, replacement, content)

content = re.sub(r'self\.\s*\n', '\n', content)

content = re.sub(r'\}\s*\}\s*\Z', '}\n', content)

with open(file_path, 'w') as f:
    f.write(content)
