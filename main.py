from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from typing import List, Set
import json
import os

@register("astrbot_plugin__group_shield", "YourName", "群聊屏蔽插件，可禁用特定群聊的LLM功能", "1.0.0")
class GroupShieldPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.shielded_groups_file = os.path.join("data", "shielded_groups.json")
        self.shielded_groups = self._load_shielded_groups()
        
    def _load_shielded_groups(self) -> Set[str]:
        """加载已屏蔽的群组列表"""
        try:
            if os.path.exists(self.shielded_groups_file):
                with open(self.shielded_groups_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
        except Exception as e:
            self.context.logger.error(f"加载屏蔽群列表失败: {e}")
        return set()
    
    def _save_shielded_groups(self):
        """保存屏蔽群列表到文件"""
        try:
            os.makedirs(os.path.dirname(self.shielded_groups_file), exist_ok=True)
            with open(self.shielded_groups_file, "w", encoding="utf-8") as f:
                json.dump(list(self.shielded_groups), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.context.logger.error(f"保存屏蔽群列表失败: {e}")
    
    @filter.command("shield_group", permission_type=filter.PermissionType.ADMIN)
    async def shield_group(self, event: AstrMessageEvent, group_id: str):
        """屏蔽指定群聊，格式：/shield_group <群号>"""
        if not group_id:
            yield event.plain_result("请提供要屏蔽的群号")
            return
            
        if group_id in self.shielded_groups:
            yield event.plain_result(f"群 {group_id} 已在屏蔽列表中")
            return
            
        self.shielded_groups.add(group_id)
        self._save_shielded_groups()
        yield event.plain_result(f"已成功屏蔽群 {group_id}")
    
    @filter.command("unshield_group", permission_type=filter.PermissionType.ADMIN)
    async def unshield_group(self, event: AstrMessageEvent, group_id: str):
        """解除屏蔽指定群聊，格式：/unshield_group <群号>"""
        if not group_id:
            yield event.plain_result("请提供要解除屏蔽的群号")
            return
            
        if group_id not in self.shielded_groups:
            yield event.plain_result(f"群 {group_id} 不在屏蔽列表中")
            return
            
        self.shielded_groups.remove(group_id)
        self._save_shielded_groups()
        yield event.plain_result(f"已解除屏蔽群 {group_id}")
    
    @filter.command("list_shielded", permission_type=filter.PermissionType.ADMIN)
    async def list_shielded_groups(self, event: AstrMessageEvent):
        """列出所有被屏蔽的群聊，格式：/list_shielded"""
        if not self.shielded_groups:
            yield event.plain_result("当前没有屏蔽任何群聊")
            return
            
        groups_list = "\n".join(sorted(self.shielded_groups))
        yield event.plain_result(f"当前屏蔽的群聊:\n{groups_list}")
    
    @filter.on_llm_request()
    async def block_llm_for_shielded_groups(self, event: AstrMessageEvent, req: ProviderRequest):
        """拦截被屏蔽群聊的LLM请求"""
        group_id = event.get_group_id()
        if group_id and group_id in self.shielded_groups:
            event.stop_event()  # 停止事件传播，阻止LLM处理
            yield event.plain_result("此群聊已被屏蔽，LLM功能不可用")
