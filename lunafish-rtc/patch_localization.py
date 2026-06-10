import re

file_path = '../reactnative-application/ios/rateme/NativeCall/Utils/LocalizationHelper.swift'
with open(file_path, 'r') as f:
    content = f.read()

# Fix currentLanguageCode reference
content = content.replace('NativeCallManager.shared.currentLanguageCode', '"en"')

# Fix value: nil, table: nil to value: "", table: nil
content = content.replace('value: nil, table: nil', 'value: "", table: nil')

with open(file_path, 'w') as f:
    f.write(content)
