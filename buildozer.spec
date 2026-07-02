[app]

# 应用基础信息
title = Cognitive Audit Engine
package.name = gcae
package.domain = org.nohn

# 版本信息（对应项目SPL V7.2正式版本）
version = 7.2.0
# Android 内部版本号，每次发布新版本递增
version.code = 1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,pdf,md,txt
source.include_patterns = assets/*,images/*
source.exclude_exts = spec
source.exclude_dirs = tests, bin, venv, .git, .github, .buildozer, __pycache__
source.exclude_patterns = license,images/*/*.jpg, *.pyc

# 入口文件
entrypoint = main.py

# 项目依赖
requirements = python3,kivy==2.3.0
# 去掉不必要的uuid-jsonl依赖，uuid是Python标准库，不需要额外安装

# 屏幕方向
orientation = portrait

# 是否全屏
fullscreen = 0

# Android 特定配置 - 使用Buildozer默认稳定版本
android.api = 33
android.ndk = 25b
android.sdk = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

# Android 权限
android.permissions = INTERNET

# Android 应用元数据
android.presplash_color = #2196F3
android.theme = @android:style/Theme.Holo.Light

# 日志配置
log_level = 2

# 构建模式（debug/release）
build_mode = debug

# 构建目录
build_dir = .buildozer
bin_dir = bin

# 不构建aab格式，只构建apk
android.release_artifact = apk
android.debug_artifact = apk

[buildozer]
# Buildozer 日志级别
log_level = 2

# 警告输出
warn_on_root = 1

# 构建超时
android.build_timeout = 1800
