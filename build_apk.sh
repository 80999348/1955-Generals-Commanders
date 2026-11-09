#!/bin/bash
set -e
SDK=/opt/android-sdk
BT=$SDK/build-tools/34.0.0
PLAT=$SDK/platforms/android-34/android.jar
APP=/root/.codebuddy/artifact/app
OUT=/root/.codebuddy/artifact/build
mkdir -p $OUT

cd $APP
# 0. 生成最新数据
python3 /root/.codebuddy/artifact/gen/gen_data.py

# 1. aapt2 编译资源
$BT/aapt2 compile --dir res -o $OUT/res.zip
# 2. 链接生成未含 dex 的 apk
$BT/aapt2 link -o $OUT/unsigned.apk -I $PLAT --manifest AndroidManifest.xml -A assets $OUT/res.zip --java $OUT/gen --auto-add-overlay
# 3. javac 编译
mkdir -p $OUT/classes
javac -source 1.8 -target 1.8 -bootclasspath $PLAT -classpath $OUT/gen -d $OUT/classes $(find src -name "*.java")
# 4. d8 转 dex
$BT/d8 --min-api 21 --lib $PLAT --output $OUT $(find $OUT/classes -name "*.class")
# 5. 加入 classes.dex
cd $OUT && zip -qj unsigned.apk classes.dex
# 6. 对齐
$BT/zipalign -f 4 unsigned.apk aligned.apk
# 7. 生成签名密钥（如不存在）
if [ ! -f keystore.jks ]; then
  keytool -genkeypair -keystore keystore.jks -alias kaijy -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass kaijy2025 -keypass kaijy2025 -dname "CN=KaiJiangLu, OU=App, O=WorkBuddy, L=SZ, S=GD, C=CN"
fi
# 8. 签名
$BT/apksigner sign --ks keystore.jks --ks-pass pass:kaijy2025 --key-pass pass:kaijy2025 --out /workspace/1955开国将帅录.apk aligned.apk
$BT/apksigner verify --print-certs /workspace/1955开国将帅录.apk | head -5
ls -la /workspace/
echo "BUILD OK"
