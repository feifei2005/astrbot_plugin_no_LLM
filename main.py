from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.provider import ProviderRequest

@register("group_block", "YourName", "屏蔽特定群聊的LLM功能", "1.0.0")
class GroupBlockPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config  # 读取配置
        self.blocked_groups = self.config.get("blocked_groups", [])

    # 拦截LLM请求
    @filter.on_llm_request()
    async def block_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        # 检查是否是群消息
        group_id = event.get_group_id()
        if not group_id:
            return  # 非群消息，不处理
        
        # 判断群ID是否在黑名单中
        if group_id in self.blocked_groups:
            # 终止事件传播，阻止后续LLM处理
            event.stop_event()
            # 可选：发送提示消息
            await event.send("该群聊已屏蔽LLM功能！")
    
    # 可选：指令添加/删除屏蔽群组
    @filter.command("block_group", alias=["屏蔽群"])
    async def add_block_group(self, event: AstrMessageEvent, group_id: str):
        if group_id not in self.blocked_groups:
            self.blocked_groups.append(group_id)
            self.config.set("blocked_groups", self.blocked_groups)
            self.config.save_config()
            yield event.plain_result(f"已屏蔽群组：{group_id}")
    
    @filter.command("unblock_group", alias=["解除屏蔽群"])
    async def remove_block_group(self, event: AstrMessageEvent, group_id: str):
        if group_id in self.blocked_groups:
            self.blocked_groups.remove(group_id)
            self.config.set("blocked_groups", self.blocked_groups)
            self.config.save_config()
            yield event.plain_result(f"已解除屏蔽群组：{group_id}")
