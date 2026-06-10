import re

file_path = '../reactnative-application/ios/rateme/NativeCall/NativeCallBridge.swift'
with open(file_path, 'r') as f:
    content = f.read()

# Fix compilation error: Value of type 'NativeCallManager' has no member 'setLanguage'
# Since we stripped setLanguage from NativeCallManager, we need to strip it or stub it in NativeCallBridge
content = re.sub(
    r'@objc func setLanguage\([\s\S]*?DispatchQueue\.main\.async \{[\s\S]*?NativeCallManager\.shared\.setLanguage\(languageCode\)[\s\S]*?resolve\(\["success": true\]\)[\s\S]*?\}',
    """@objc func setLanguage(_ languageCode: String,
                          resolver resolve: @escaping RCTPromiseResolveBlock,
                          rejecter reject: @escaping RCTPromiseRejectBlock) {
        resolve(["success": true])
    }""",
    content
)

with open(file_path, 'w') as f:
    f.write(content)
