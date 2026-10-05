# Skills Catalog

本目录收录本机 `~/.codex/skills` 与 `~/.agents/skills` 中的个人 skill，并保留项目原有的 `teach` 定制版本。

当前共 **64** 个 skill。来源表示同步前本机所在目录；`teach` 标为项目定制版，因为保留了比本机副本更完整的内容。

## 支付与账户

| Skill | 用途 | 本机来源 |
|---|---|---|
| [`alipay-authenticate-wallet`](skills/alipay-authenticate-wallet/SKILL.md) | 支付宝官方 AI 支付能力开通与授权技能。用于独立钱包申请开通、查询授权状态、提交开通口令、提交授权码、确认支付宝侧操作结果、关闭授权，以及支付命令明确转交的钱包处理；“用户账号 token”“账号 token”“口令码”“开通码”“enrollment code”也触发。收银台、订单或协议支付仍由支付技能处理。关键词：开通、授权、绑定、解绑、支付能力、支付功能、用户账号token、口令码、开通码、enrollment code、验证码 | `~/.codex/skills/alipay-authenticate-wallet` |
| [`alipay-payment-skill`](skills/alipay-payment-skill/SKILL.md) | 支付宝官方支付处理技能。覆盖收银台支付、HTTP 402 协议支付、问题反馈全场景。当以下任一情况出现时必须调用此技能：1. 用户提供或上下文中存在 cashier*.alipay.com、excashier.alipay.com、qr.alipay.com 或 tbapi* 域名的 URL、支付宝订单号或订单串；2. 任何工具/技能/API 返回结果中包含支付宝收银台链接、支付宝订单号或订单串，或包含"请使用支付宝支付"等支付指引；3 | `~/.codex/skills/alipay-payment-skill` |
| [`skillpay-onboarding`](skills/skillpay-onboarding/SKILL.md) | 根据用户明确提供的商品标识（merchant_id/product_id）购买、支付恢复并通过支付宝 skillpay 完成 Skill 履约、安装和验证。仅用于本地 Skill 安装流程；用户要求通过 curl 读取 skillpay/ct URL 并按 URL 返回指引购买安装时，继续使用线上购买模式，不由本 Skill 接管。 | `~/.codex/skills/skillpay-onboarding` |

## 设计与前端

| Skill | 用途 | 本机来源 |
|---|---|---|
| [`animate`](skills/animate/SKILL.md) | Build an animation from scratch, making the decisions in the order that determines whether it feels right — should it animate at all, what purpose, which tool, which properties, which curve and duration, how it interrupt | `~/.codex/skills/animate` |
| [`animate-expo`](skills/animate-expo/SKILL.md) | Build animations in React Native and Expo, making the decisions in the order that determines whether they feel right — should it animate, which thread it runs on, which properties, spring or timing, how the gesture hands | `~/.codex/skills/animate-expo` |
| [`animation-vocabulary`](skills/animation-vocabulary/SKILL.md) | Reverse-lookup glossary that turns a vague description of a web animation or motion effect into its exact term ("the bouncy thing when a popover opens" → Pop in; "the iOS rubber-band scroll" → Rubber-banding). Use when t | `~/.codex/skills/animation-vocabulary` |
| [`apple-design`](skills/apple-design/SKILL.md) | Apple's approach to interface design and fluid, physical motion, translated for the web. Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible tran | `~/.codex/skills/apple-design` |
| [`ask-sonner`](skills/ask-sonner/SKILL.md) | Guide to Sonner, the React toast library — install and wire up the Toaster, pick the right toast() call, promise and loading toasts, updating, dismissing and persisting toasts, styling, theming and icons, positioning and | `~/.codex/skills/ask-sonner` |
| [`emil-design-eng`](skills/emil-design-eng/SKILL.md) | This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great. | `~/.codex/skills/emil-design-eng` |
| [`find-animation-opportunities`](skills/find-animation-opportunities/SKILL.md) | Search a codebase or UI for places that don't animate but should, and reject everything that shouldn't. Read-only; it proposes motion with exact values, it does not implement it. Use when the user asks "what could be ani | `~/.codex/skills/find-animation-opportunities` |
| [`improve-animations`](skills/improve-animations/SKILL.md) | Survey a codebase's animation and motion code as a senior motion advisor, then produce a prioritized audit and self-contained implementation plans for other agents (or cheaper models) to execute. Read-only on source code | `~/.codex/skills/improve-animations` |
| [`pick-ui-library`](skills/pick-ui-library/SKILL.md) | Pick the right library for a given frontend task from a curated, opinionated list — numbers, OTP inputs, charts, command menus, virtualization, drag and drop, toasts, state, styling, and more. Only runs when explicitly i | `~/.codex/skills/pick-ui-library` |
| [`prototype`](skills/prototype/SKILL.md) | Build multiple genuinely different versions of a UI piece you describe, rendered behind a visual picker so you can flip through them live and promote the one that feels right. Only runs when explicitly invoked; it does n | `~/.codex/skills/prototype` |
| [`review-animations`](skills/review-animations/SKILL.md) | Reviews animation and motion code against a high craft bar derived from Emil Kowalski's design engineering philosophy. Default to flagging; approval is earned. | `~/.codex/skills/review-animations` |

## 工程与研发

| Skill | 用途 | 本机来源 |
|---|---|---|
| [`atomic-step-commit`](skills/atomic-step-commit/SKILL.md) | Use when preparing, splitting, staging, or creating git commits for completed work, especially when changes span multiple concerns, tests, files, or behavioral units and each commit should be independently reviewable and | `~/.codex/skills/atomic-step-commit` |
| [`boji`](skills/boji/SKILL.md) | Use when the user invokes $boji, asks for 薄肌模式, or wants playful 邵艾伦式闲聊或角色扮演。仅仅提到薄肌、健身或邵艾伦来询问事实、讨论或修改本 skill 时不要触发。 | `~/.codex/skills/boji` |
| [`frontier-engineering-research`](skills/frontier-engineering-research/SKILL.md) | Use when researching current engineering solutions, comparing tools or architectures, tracking frontier engineering thinking, or needing high-signal X-first sources for modern software decisions. | `~/.codex/skills/frontier-engineering-research` |
| [`receiving-code-review`](skills/receiving-code-review/SKILL.md) | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind  | `~/.codex/skills/receiving-code-review` |
| [`systematic-debugging`](skills/systematic-debugging/SKILL.md) | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes | `~/.codex/skills/systematic-debugging` |
| [`test-driven-development`](skills/test-driven-development/SKILL.md) | Use when implementing any feature or bugfix, before writing implementation code | `~/.codex/skills/test-driven-development` |
| [`using-git-worktrees`](skills/using-git-worktrees/SKILL.md) | Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback | `~/.codex/skills/using-git-worktrees` |
| [`write-swift`](skills/write-swift/SKILL.md) | How to write modern Swift well — modeling with value types, Swift 6 data-race safety and approachable concurrency (@concurrent, main-actor-by-default, actors, task groups), protocols and generics (some vs any), API desig | `~/.codex/skills/write-swift` |
| [`writing-skills`](skills/writing-skills/SKILL.md) | Use when creating new skills, editing existing skills, or verifying skills work before deployment | `~/.codex/skills/writing-skills` |

## 产品与内容

| Skill | 用途 | 本机来源 |
|---|---|---|
| [`blindbox-ip-skill-4styles`](skills/blindbox-ip-skill-4styles/SKILL.md) | Create a reusable content-illustration character and simple IP Standard Pack for a person, creator account, or brand. Use for personal IP, account mascots, brand characters, blind-box or designer-toy characters, “把我变成一个角 | `~/.codex/skills/blindbox-ip-skill-4styles` |
| [`brainstorm-experiments-new`](skills/brainstorm-experiments-new/SKILL.md) | Design lean startup experiments (pretotypes) for a new product. Creates XYZ hypotheses and suggests low-effort validation methods like landing pages, explainer videos, and pre-orders. Use when validating a new product id | `~/.codex/skills/brainstorm-experiments-new` |
| [`brainstorm-ideas-new`](skills/brainstorm-ideas-new/SKILL.md) | Brainstorm feature ideas for a new product in initial discovery from PM, Designer, and Engineer perspectives. Use when starting product discovery for a new product, exploring features for a startup idea, or doing initial | `~/.codex/skills/brainstorm-ideas-new` |
| [`build-personal-profile`](skills/build-personal-profile/SKILL.md) | Use when 用户希望生成或更新自己的综合个人画像、自我介绍档案，尤其要求交付本地可交互网页时。 | `~/.codex/skills/build-personal-profile` |
| [`creating-xiaohongshu-posts`](skills/creating-xiaohongshu-posts/SKILL.md) | Use when the user wants to plan, write, rewrite, package, or publish a Xiaohongshu/小红书/RedNote post from an idea, rough notes, product, or personal experience. | `~/.codex/skills/creating-xiaohongshu-posts` |
| [`identify-assumptions-new`](skills/identify-assumptions-new/SKILL.md) | Identify risky assumptions for a new product idea across 8 risk categories including Go-to-Market, Strategy, and Team. Use when evaluating startup risks, assessing a new product concept, or mapping assumptions for a new  | `~/.codex/skills/identify-assumptions-new` |
| [`monetization-strategy`](skills/monetization-strategy/SKILL.md) | Brainstorm 3-5 monetization strategies with audience fit, risks, and validation experiments. Use when exploring revenue models, evaluating pricing strategies, or deciding how to monetize a product. | `~/.codex/skills/monetization-strategy` |

## 协作与表达

| Skill | 用途 | 本机来源 |
|---|---|---|
| [`grill-me`](skills/grill-me/SKILL.md) | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions  | `~/.codex/skills/grill-me` |
| [`grill-with-docs`](skills/grill-with-docs/SKILL.md) | Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates documentation (CONTEXT.md, ADRs) inline as decisions crystallise. Use when user wants to stress-test a plan  | `~/.codex/skills/grill-with-docs` |
| [`how`](skills/how/SKILL.md) | Explain how something works in this codebase by exploring code and producing a clear architectural explanation. Optionally critique the architecture for issues. | `~/.codex/skills/how` |
| [`lieflat-less-ai-tone`](skills/lieflat-less-ai-tone/SKILL.md) | 按 SKILL.md 明确列出的规则识别并改写写作中的 AI 痕迹。只能处理清单内的问题；未命中规则的文字必须原样保留，也不能改变文章框架。适用于写作完成后的成稿清理。 Remove AI writing tells using an explicit whitelist of rules; leaves unmatched text untouched. | `~/.codex/skills/lieflat-less-ai-tone` |
| [`planning-with-files`](skills/planning-with-files/SKILL.md) | Implements Manus-style file-based planning to organize and track progress on complex tasks. Creates task_plan.md, findings.md, and progress.md. Use when asked to plan out, break down, or organize a multi-step project, re | `~/.codex/skills/planning-with-files` |
| [`show-me`](skills/show-me/SKILL.md) | Help the user understand the current topic visually with concise diagrams, code-shape sketches, and focused HTML artifacts. | `~/.codex/skills/show-me` |
| [`teach`](skills/teach/SKILL.md) | Teach the user a new skill or concept, within this workspace. | 项目定制版（保留） |

## 飞书与 Lark

| Skill | 用途 | 本机来源 |
|---|---|---|
| [`lark-approval`](skills/lark-approval/SKILL.md) | 飞书审批：查询和处理审批待办/已办/实例，搜索可发起审批定义、查看定义详情并发起原生审批实例。当用户要处理审批任务、查看审批实例、搜索或发起审批时使用。审批待办不是飞书任务；非审批类待办走 lark-task。不负责创建审批定义；三方审批定义不走原生提单。 | `~/.agents/skills/lark-approval` |
| [`lark-apps`](skills/lark-apps/SKILL.md) | 妙搭（Spark/Miaoda）应用开发与托管：应用创建、本地全栈开发、云端生成迭代、创意设计（UI mockup / 可交互原型 / 线框图 / 落地页 / 仪表盘 / 幻灯片 deck / 视觉探索）、AI相关能力和飞书平台能力或者其他外部能力集成、日志/Trace/监控指标/PV/UV 查询、环境变量管理、应用角色与成员管理、自动化触发器（定时/记录变更/Webhook/飞书审批）。当用户要开发/新建一个系统·工具·平台·应用，或 | `~/.agents/skills/lark-apps` |
| [`lark-attendance`](skills/lark-attendance/SKILL.md) | 飞书考勤打卡：查询自己的考勤打卡记录 | `~/.agents/skills/lark-attendance` |
| [`lark-base`](skills/lark-base/SKILL.md) | 飞书多维表格（Base）操作：建表、字段、记录、视图、统计、公式/lookup、表单、仪表盘、workflow、角色权限；遇到 Base/多维表格/bitable 或 /base/ 链接时使用。文件导入转 lark-drive，认证/授权转 lark-shared。 | `~/.agents/skills/lark-base` |
| [`lark-calendar`](skills/lark-calendar/SKILL.md) | 飞书日历：管理日历日程和会议室。查看/搜索日程、创建/更新日程、管理参会人、查询忙闲和推荐时段、预定会议室。当用户需要查看日程安排、创建/修改会议、查询/预定会议室时使用。不负责：查询过去的视频会议记录（走 lark-vc）、待办任务（走 lark-task）。 | `~/.agents/skills/lark-calendar` |
| [`lark-contact`](skills/lark-contact/SKILL.md) | 飞书 / Lark 通讯录:按姓名 / 邮箱解析成 open_id,或按 open_id 反查姓名 / 部门 / 邮箱 / 联系方式 / 个人状态 / 签名。当用户提到某人姓名要下一步发消息 / 排日程,或拿到 open_id 想查具体信息时使用。不负责部门树遍历、按部门列员工、组织架构图,这类需求走原生 OpenAPI。 | `~/.agents/skills/lark-contact` |
| [`lark-doc`](skills/lark-doc/SKILL.md) | 飞书云文档（Docx / Wiki 文档）：读取和编辑飞书文档内容。当用户给出文档 URL 或 token，或需要查看、创建、编辑文档、插入或下载文档图片附件时使用。文档中嵌入的电子表格、多维表格、画板，先用本 skill 提取 token 再切到对应 skill。当用户给出 doubao.com 的 /docx/ 或 /wiki/ URL/token 时，也应直接使用本 skill；路由依据是 URL 路径模式和 token，而不是域 | `~/.agents/skills/lark-doc` |
| [`lark-drive`](skills/lark-drive/SKILL.md) | 飞书云空间（云盘/云存储）：管理 Drive 文件和文件夹，包含上传/下载、创建文件夹、复制/移动/删除、查看元数据、评论/权限/订阅、标题、版本、飞书文档密级标签（secure labels）和本地文件导入。用户需要整理云盘目录、处理云空间资源 URL/token、判断链接类型/真实 token/标题，或导入 Word/Markdown/Excel/CSV/PPTX/.base 为 docx/sheet/bitable/slides  | `~/.agents/skills/lark-drive` |
| [`lark-event`](skills/lark-event/SKILL.md) | Lark/Feishu real-time event listening / subscribing / consuming: stream events as NDJSON via `lark-cli event consume <EventKey>` (covers IM messages/reactions/chat changes, Approval status changes, Task updates, VC meeti | `~/.agents/skills/lark-event` |
| [`lark-im`](skills/lark-im/SKILL.md) | 飞书即时通讯：收发消息和管理群聊。发送和回复消息、搜索聊天记录、管理群聊成员、上传下载图片和文件（支持大文件分片下载）、管理表情回复、发送应用内/短信/电话加急、发送和处理交互卡片（Interactive Card）、监听卡片按钮回调（card.action.trigger）。当用户需要发消息、查看或搜索聊天记录、下载聊天中的文件、查看群成员、搜索群、创建群聊或话题群、管理标记数据、管理 Feed 置顶（添加/移除/查询置顶会话）、管理 | `~/.agents/skills/lark-im` |
| [`lark-mail`](skills/lark-mail/SKILL.md) | 飞书邮箱：Use when user mentions 起草邮件、写邮件、草稿、发送/回复/转发邮件、查阅邮件、看邮件、搜索邮件、邮件文件夹、邮件标签、邮件联系人、监听新邮件、邮件收信规则等；use for mail/email intent only. Do not use for docs/sheets/calendar/auth setup/pure contact lookup/IM chat tasks. | `~/.agents/skills/lark-mail` |
| [`lark-markdown`](skills/lark-markdown/SKILL.md) | 飞书 Markdown：查看、创建、上传、编辑和比较 Markdown 文件。当用户需要创建或编辑 Markdown 文件、读取、修改、局部 patch 或比较差异时使用。不负责将 Markdown 导入为飞书在线文档，也不负责文件搜索、权限、评论、移动、删除等云空间管理操作。 | `~/.agents/skills/lark-markdown` |
| [`lark-minutes`](skills/lark-minutes/SKILL.md) | 飞书妙记：搜索妙记、查看妙记基础信息、下载/上传音视频、读取或编辑妙记的产物内容、改标题、替换说话人/关键词、申请妙记查看/编辑权限。当给出minute_token、本地音视频文件，要查/改/转妙记产物，或用户明确要主动申请妙记权限时使用；本地音视频转纪要/逐字稿优先走本 skill，不要用 ffmpeg/whisper 本地转写。不负责：获取会议关联妙记，或仅按自然语言标题定位纪要 | `~/.agents/skills/lark-minutes` |
| [`lark-note`](skills/lark-note/SKILL.md) | 飞书会议纪要（Note）直查：已知 note_id 时查询纪要详情、展示类型、关联文档 token，并读取 unified 原始逐字记录。当用户已持有 note_id，或从文档显式 vc-node-id 获得 note_id 时使用。不负责会议/日程/妙记定位、文档标题搜索或 Docx 正文读取。 | `~/.agents/skills/lark-note` |
| [`lark-okr`](skills/lark-okr/SKILL.md) | 飞书 OKR：管理目标与关键结果。查看和编辑 OKR 周期、目标、关键结果、对齐关系、量化指标和进展记录。当用户需要查看或创建 OKR、管理目标和关键结果、查看对齐关系时使用。不负责：待办任务管理（lark-task）、日程/会议安排（lark-calendar）、绩效评估 | `~/.agents/skills/lark-okr` |
| [`lark-openapi-explorer`](skills/lark-openapi-explorer/SKILL.md) | 飞书/Lark 原生 OpenAPI 探索：从官方文档库中挖掘未经 CLI 封装的原生 OpenAPI 接口。当用户的需求无法被现有 lark-* skill 或 lark-cli 已注册命令满足，需要查找并调用原生飞书 OpenAPI 时使用。 | `~/.agents/skills/lark-openapi-explorer` |
| [`lark-shared`](skills/lark-shared/SKILL.md) | Use for lark-cli setup/auth tasks: auth login/status/logout, user vs bot identity, business-domain permissions (--domain, including all/docs/drive), missing scopes, revoking authorization, or handling _notice JSON. | `~/.agents/skills/lark-shared` |
| [`lark-sheets`](skills/lark-sheets/SKILL.md) | 飞书电子表格：创建和操作电子表格。支持创建表格、管理工作表与行列结构（增删/合并/调整尺寸/隐藏/冻结）、读写单元格（值/公式/样式/批注/单元格图片）、查找替换、多操作原子批量更新，以及图表、透视表、条件格式、筛选器、迷你图、浮动图片等对象的创建与维护。当用户需要创建电子表格、管理工作表、批量读写或编辑数据、统计汇总与可视化、表格美化、公式计算（含 Excel 公式迁移）、金融/财务建模（DCF、三张表、预算、Sensitivity  | `~/.agents/skills/lark-sheets` |
| [`lark-skill-maker`](skills/lark-skill-maker/SKILL.md) | 创建 lark-cli 的自定义 Skill。当用户需要把飞书 API 操作封装成可复用的 Skill（包装原子 API 或编排多步流程）时使用。 | `~/.agents/skills/lark-skill-maker` |
| [`lark-slides`](skills/lark-slides/SKILL.md) | 飞书幻灯片：创建和编辑幻灯片。创建演示文稿、读取幻灯片内容、管理幻灯片页面（创建、删除、读取、局部替换）。当用户需要创建或编辑幻灯片、读取或修改单个页面时使用。当用户给出 doubao.com 的 /slides/ URL/token 时，也应直接使用本 skill，不要因为域名不是飞书而回退到 WebFetch；路由依据是 URL 路径模式和 token，而不是域名。不负责：云文档内容编辑（走 lark-doc）、云文档里的独立画板对 | `~/.agents/skills/lark-slides` |
| [`lark-task`](skills/lark-task/SKILL.md) | 飞书任务：管理任务、清单和任务智能体。创建待办任务、查看和更新任务状态、拆分子任务、组织任务清单、分配协作成员、上传任务附件、注册或注销任务智能体、更新任务智能体的主页数据、写入智能体任务记录。当用户需要创建待办事项、查看任务列表、跟踪任务进度、管理项目清单或给他人分配任务、为任务上传附件文件、注册注销任务智能体、更新智能体主页数据、写入任务记录时使用。 | `~/.agents/skills/lark-task` |
| [`lark-vc`](skills/lark-vc/SKILL.md) | 飞书视频会议：搜索历史会议记录、查询会议纪要（总结/待办/章节/逐字稿）、查询参会人快照。当用户查询已结束的会议、获取会议产物（纪要/妙记）、查看参会人时使用；查询未来日程走 lark-calendar。不负责：Agent 真实入会/离会、会中实时事件（走 lark-vc-agent）。 | `~/.agents/skills/lark-vc` |
| [`lark-vc-agent`](skills/lark-vc-agent/SKILL.md) | 飞书视频会议会中能力：用于让应用机器人真实加入或离开正在进行的会议，并读取当前身份可见的会中事件、发送会中文本消息或会中表情。适用于用户询问正在开的会议发生了什么、谁在发言、是否共享内容，或需要发现当前可读的进行中会议 ID。不负责已结束会议搜索、参会人快照、纪要、逐字稿或录制查询，这些使用 lark-vc 技能。 | `~/.agents/skills/lark-vc-agent` |
| [`lark-whiteboard`](skills/lark-whiteboard/SKILL.md) | 飞书画板：查询和编辑飞书云文档中的画板。支持导出画板为预览图片、导出原始节点结构、使用多种格式更新画板内容。 当用户需要查看画板内容、导出画板图片、编辑画板时使用此 skill。不负责：飞书云文档内容编辑（lark-doc）、文档内嵌电子表格/Base（lark-sheets / lark-base）。 | `~/.agents/skills/lark-whiteboard` |
| [`lark-wiki`](skills/lark-wiki/SKILL.md) | 飞书知识库：管理知识空间、空间成员和文档节点。创建和查询知识空间、查看和管理空间成员、管理节点层级结构、在知识库中组织文档和快捷方式。当用户需要在知识库中查找或创建文档、浏览知识空间结构、查看或管理空间成员、移动或复制节点时使用。当用户给出 doubao.com 的 /wiki/ URL/token 时，也应直接使用本 skill，不要因为域名不是飞书而回退到 WebFetch；路由依据是 URL 路径模式和 token，而不是域名。不 | `~/.agents/skills/lark-wiki` |
| [`lark-workflow-meeting-summary`](skills/lark-workflow-meeting-summary/SKILL.md) | 会议纪要整理工作流：汇总指定时间范围内的会议纪要并生成结构化报告。当用户需要整理会议纪要、生成会议周报、回顾一段时间内的会议内容时使用。 | `~/.agents/skills/lark-workflow-meeting-summary` |
| [`lark-workflow-standup-report`](skills/lark-workflow-standup-report/SKILL.md) | 日程待办摘要：编排 calendar +agenda 和 task +get-my-tasks，生成指定日期的日程与未完成任务摘要。适用于了解今天/明天/本周的安排。 | `~/.agents/skills/lark-workflow-standup-report` |
