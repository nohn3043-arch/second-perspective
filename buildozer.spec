[app]
title = CognitiveAuditEngine
package.name = cognitive_audit_engine
package.domain = ai.nohn
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = main.py,*.kv
version = 0.1
requirements = python3,kivy,hostpython3,pyjnius,android
orientation = portrait

# Android settings
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
android.accept_sdk_license = True
android.use_aapt2 = True
android.gradle_dependencies = []

# Logging
log_level = 2
