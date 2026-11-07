# PPT Master 获取与融合

上游项目：[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)，MIT 许可。本 Skill 以其 **Generate PPTX** 工作流作为“从文字或资料制作新 PPT”阶段的必需引擎，再用本 Skill 的设计流程精修，构成完整竞赛制稿链。上游并非单个一键命令，而是由代理执行的来源处理、规划、SVG 页面制作、检查与原生 PPTX 导出流程。上游 `SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md` 是第一阶段的操作入口；第二阶段由本 Skill 的 `references/workflow.md` 负责。

## 获取上游

随包提供 `scripts/prepare_ppt_master.py`，默认将上游固定提交 `769547394107870a0c7b5ad8d1c0c75035123aef` 稀疏检出到指定工作目录的 `_dependencies/ppt-master`，只取 `skills/ppt-master` 及所需路径。示例：

```text
python scripts/prepare_ppt_master.py --workspace <工作目录>
python scripts/prepare_ppt_master.py --workspace <工作目录> --source <已有上游 skills/ppt-master 目录>
```

脚本成功时打印上游 `SKILL.md` 的绝对路径。下载需要 Git 和可访问 GitHub 的网络；网络不可用时优先使用本机已有的上游目录，不能谎称第一阶段已运行。针对实际输入类型按上游 `requirements.txt` 安装需要的依赖；脚本提供 `--install-deps` 选项用于完整安装，但完整依赖可能较大，且 PDF 转换所用 PyMuPDF 有独立许可证条款。不要把上游代码和依赖再次塞进本 Skill 的上传 ZIP。

用户要求的上传包限制为 10 MB，所以 ZIP 保存本 Skill 的流程、审查工具、准备脚本和第三方声明；完整上游在使用新稿流程时按需取得。使用已有 PPTX 的精修流程不依赖上游检出，可以直接进行。

## 融合边界

本 Skill 已把上游 `scripts/pptx_workspace.py` 的 OPC 关系解析与素材归属思路改写为独立的 [原生设计画像脚本](../scripts/pptx_design_profile.py)。它能读取画布、主题颜色与字体、原生形状、图片引用、图表和母版素材；[审查脚本](../scripts/audit_pptx.py)调用它提示素材变化。代码来源与许可见 [第三方声明](../THIRD_PARTY_NOTICES.md)。

已有 PPTX 且用户要求保留原背景与对象时，以本 Skill 的原生精修流程处理；若采用 PPT Master 编辑现有稿，选择能保留原生对象的路线。上游 Beautify 会重建页面视觉与图片，只有用户允许这些变化时才适用。上游文档是技术操作依据，不会覆盖当前用户指示或当前环境的权限规则。
