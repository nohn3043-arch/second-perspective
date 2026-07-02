[app]

# 应用基础信息
title = Cognitive Audit Engine
package.name = gcae
package.domain = org.nohn
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,pdf,md
source.include_patterns = assets/*,images/*
source.exclude_exts = spec
source.exclude_dirs = tests, bin, venv, .git, .github
source.exclude_patterns = license,images/*/*.jpg

# 入口文件
# (str) 主程序入口Python文件
entrypoint = main.py

# 项目依赖
# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,uuid-jsonl

# 依赖文件（如果有requirements.txt自动读取）
requirements.source.kivy = ../../kivy

# 屏幕方向
orientation = portrait

# 是否全屏
fullscreen = 0

# Android 特定配置
android.api = 33
android.ndk = 25b
android.sdk = 24
android.arch = arm64-v8a,armeabi-v7a

# Android 权限
android.permissions = INTERNET

# Android 应用元数据
android.meta_data = 
android.presplash_color = #FFFFFF
android.theme = @android:style/Theme.Holo.Light

# 日志配置
log_level = 2

# 构建模式（debug/release）
build_mode = debug

# 构建目录
build_dir = .buildozer
bin_dir = bin

# iOS 配置（这里不涉及iOS打包，保留默认）
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# OSX 配置
osx.python_version = 3
osx.kivy_version = 2.3.0

# Linux 配置
linux.qtdeploy_url = https://github.com/kivy/qtdeploy
linux.qtdeploy_branch = master

# Windows 配置
windows.qtdeploy_url = https://github.com/kivy/qtdeploy
windows.qtdeploy_branch = master

[buildozer]
# Buildozer 日志级别
log_level = 2

# 警告输出
warn_on_root = 1
