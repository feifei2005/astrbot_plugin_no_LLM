from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import json
import os

@register("block_group", "YourName", "屏蔽指定群组的LLM响应", "1.0.0")
class BlockGroupPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.blocked_groups = set()
        self.config_path = os.path.join("data", "blocked_groups.json")
        self._load_config()

    def _load_config(self):
        """加载已屏蔽的群组列表"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.blocked_groups = set(json.load(f))
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def _save_config(self):
        """保存屏蔽群组列表"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(list(self.blocked_groups), f)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    @filter.command("blockgroup", permission_type=filter.PermissionType.ADMIN)
    async def block_group(self, event: AstrMessageEvent, group_id: str):
        """添加群组到屏蔽列表"""
        self.blocked_groups.add(group_id)
        self._save_config()
        yield event.plain_result(f"已屏蔽群组 {group_id}")

    @filter.command("unblockgroup", permission_type=filter.PermissionType.ADMIN)
    async def unblock_group(self, event: AstrMessageEvent, group_id: str):
        """从屏蔽列表移除群组"""
        if group_id in self.blocked_groups:
            self.blocked_groups.remove(group_id)
            self._save_config()
            yield event.plain_result(f"已解除屏蔽群组 {group_id}")
        else:
            yield event.plain_result(f"该群组未在屏蔽列表中")

    @filter.on_llm_request()
    async def block_llm_request(self, event: AstrMessageEvent, req):
        """拦截LLM请求"""
        group_id = event.get_group_id()
        if group_id and group_id in self.blocked_groups:
            event.stop_event()
            yield event.plain_result("本群已禁用LLM功能")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def check_group_message(self, event: AstrMessageEvent):
        """拦截群消息事件"""
        group_id = event.get_group_id()
        if group_id in self.blocked_groups:
            event.stop_event()

    async def terminate(self):
        """插件卸载时保存配置"""
        self._save_config()
