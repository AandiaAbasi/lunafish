import re

file_path = '../reactnative-application/ios/rateme/NativeCall/Services/NativeCallManager.swift'
with open(file_path, 'r') as f:
    content = f.read()

content = re.sub(r'// Now initialize Agora\s*if !self\.false \{[\s\S]*?self\.\s*\}', '', content)

content = re.sub(r'func toggleMute\(\) -> Bool \{ return false \}\s*return result\s*\}\s*let newMuteState = (.*?)\s*\}', 'func toggleMute() -> Bool { return false }', content, flags=re.DOTALL)
content = re.sub(r'func toggleSpeaker\(\) -> Bool \{ return false \}\s*return result\s*\}\s*return (.*?)\s*\}', 'func toggleSpeaker() -> Bool { return false }', content, flags=re.DOTALL)
content = re.sub(r'func toggleVideo\(\) -> Bool \{ return false \}\s*return result\s*\}\s*return (.*?)\s*\}', 'func toggleVideo() -> Bool { return false }', content, flags=re.DOTALL)
content = re.sub(r'func switchCamera\(\) \{\}\s*return\s*\}\s*(.*?)\s*\}', 'func switchCamera() {}', content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)
