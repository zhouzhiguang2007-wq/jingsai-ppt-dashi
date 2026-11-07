# 与 PPT Master 的融合范围

上游项目：[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)，MIT 许可，检查时的 main 提交为 `769547394107870a0c7b5ad8d1c0c75035123aef`。本 Skill 保留已有竞赛设计流程，并把上游 `scripts/pptx_workspace.py` 的 OPC 关系解析与素材归属思路改写为独立的 [原生设计画像脚本](../scripts/pptx_design_profile.py)。脚本无需上游依赖，可识别画布、主题颜色与字体、逐页原生形状、图片引用、图表和母版关联素材；[审查脚本](../scripts/audit_pptx.py)已调用它，提示可能丢失或重编码的素材。版权与许可见 [第三方声明](../THIRD_PARTY_NOTICES.md)。

上游完整引擎约有大量模块和素材，不放进这个可直接上传的 Skill ZIP。若本机已有上游检出，且任务需要它的原生回写、复杂可编辑形状或完整交付检查，可按上游 `skills/ppt-master/SKILL.md` 的兼容方式调用其 `Edit Native PPTX` 路线，或运行 `scripts/pptx_intake.py`、`scripts/pptx_delivery_check.py`。先确认上游依赖能在当前环境运行，再在原稿副本上试一页，最后逐页核对。没有上游检出时，本 Skill 的设计画像、内容审查和 PowerPoint 渲染流程仍可独立工作。

上游的 `Beautify PPTX` 路线会重建页面视觉和图片。用户要求保留原底纹、校徽与证据图时，以保留原生对象的编辑方式执行；只有用户明确允许重建背景与素材时，才考虑整套重排路线。上游文档中的确认门槛和工具约束属于其项目流程，不能替代当前用户的要求或授权。
