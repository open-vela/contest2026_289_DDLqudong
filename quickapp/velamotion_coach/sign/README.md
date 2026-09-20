# 本地发布签名

提交包自带已签名的生产 RPK，可直接安装。原作者私钥不公开。

如需重建 release，在 AIoT-IDE 打开快应用工程，点击“发布”并填写签名信息，工具将在 `sign/release/` 生成 `private.pem` 与 `certificate.pem`，然后执行 `npm run release`。新签名与原签名不同，安装时可能需要先卸载旧包；保留所需本地训练记录后再操作。

该目录下的 PEM 文件被 Git 忽略，不进入 ZIP。
