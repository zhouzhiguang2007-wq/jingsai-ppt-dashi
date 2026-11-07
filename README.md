# 竞赛ppt大师

从用户的文字要求、主题或资料出发，完成两阶段竞赛 PPT 制作：

1. **PPT Master 制作可编辑初稿**：整理文字与事实约束，使用 [PPT Master](https://github.com/hugohe3/ppt-master) 的 Generate PPTX 流程进行内容组织、页面设计、检查和原生 PPTX 导出。
2. **竞赛ppt大师逐页精修**：根据用户的比赛场景和风格要求，优化叙事结构、标题层级、箭头、图形、色彩、证据图和版面，逐页渲染并核对内容与素材，交付竞赛成品。

用户已有 PPTX 且只要优化时，直接进入第二阶段。用户要求文字或数据不变时，两阶段都要遵守；用户要求保留背景、照片、标志时，精修不能把它们换成纯白板或无依据的示意图。

## 使用

直接下载 [可上传的 Skill ZIP](competition-ppt-polish.zip)；压缩包仅有一个顶层文件夹 `competition-ppt-polish`，其中根目录即 [SKILL.md](SKILL.md)。给代理提供文字要求、参考资料或现有 PPTX，并说明赛事、页数、演讲时长、风格和必须保留的内容（有则提供）；无需先自己做初稿。

从文字新建 PPT 时，本 Skill 的 [准备脚本](scripts/prepare_ppt_master.py)可在工作目录中按需取得固定版本的完整 PPT Master，或接入本机已有的上游目录。完整 PPT Master 引擎不放入此仓库的 Skill 上传 ZIP；下载需要 Git 与 GitHub 网络，所需 Python 依赖按实际任务安装。上游是由代理执行的制稿工作流，准备脚本只负责获取与定位，不会单独生成 PPTX。

- 两阶段全流程：[references/full-pipeline.md](references/full-pipeline.md)
- 竞赛精修流程：[references/workflow.md](references/workflow.md)
- PPT Master 获取与融合：[references/ppt-master-integration.md](references/ppt-master-integration.md)
- 浅蓝工程竞赛稿偏好：[references/design-profile.md](references/design-profile.md)
- 其他场景经验：[references/scenario-lessons.md](references/scenario-lessons.md)
- 原生设计画像：[scripts/pptx_design_profile.py](scripts/pptx_design_profile.py)
- 内容与素材审查：[scripts/audit_pptx.py](scripts/audit_pptx.py)

本仓库采用 [MIT License](LICENSE)；上游代码来源见 [第三方声明](THIRD_PARTY_NOTICES.md)。
