from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from typing import Set

@register("astrbot_plugin_block_group", "YourName", "群聊屏蔽插件", "1.0.0", "https://github.com/your_repo")
class BlockGroupPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.blocked_groups: Set[str] = set()
        
        # 从文件加载已屏蔽的群组
        self.load_blocked_groups()
    
    def load_blocked_groups(self):
        """从文件加载已屏蔽的群组列表"""
        try:
            with open("data/blocked_groups.txt", "r", encoding="utf-8") as f:
                self.blocked_groups = set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            self.blocked_groups = set()
    
    def save_blocked_groups(self):
        """保存屏蔽群组列表到文件"""
        with open("data/blocked_groups.txt", "w", encoding="utf-8") as f:
            for group_id in self.blocked_groups:
                f.write(f"{group_id}\n")
    
    @filter.command("block_group", permission_type=filter.PermissionType.ADMIN)
    async def block_group(self, event: AstrMessageEvent, group_id: str = None):
        """屏蔽指定群组，使其无法使用LLM功能
        
        Args:
            group_id (str): 要屏蔽的群组ID。如果不提供，则屏蔽当前群组。
        """
        if not group_id:
            if not event.get_group_id():
                yield event.plain_result("请在群聊中使用此命令或提供群组ID")
                return
            group_id = event.get_group_id()
        
        if group_id in self.blocked_groups:
            yield event.plain_result(f"群组 {group_id} 已在屏蔽列表中")
            return
        
        self.blocked_groups.add(group_id)
        self.save_blocked_groups()
        yield event.plain_result(f"已屏蔽群组 {group_id}")
    
    @filter.command("unblock_group", permission_type=filter.PermissionType.ADMIN)
    async def unblock_group(self, event: AstrMessageEvent, group_id: str = None):
        """解除屏蔽指定群组
        
        Args:
            group_id (str): 要解除屏蔽的群组ID。如果不提供，则解除当前群组。
        """
        if not group_id:
            if not event.get_group_id():
                yield event.plain_result("请在群聊中使用此命令或提供群组ID")
                return
            group_id = event.get_group_id()
        
        if group_id not in self.blocked_groups:
            yield event.plain_result(f"群组 {group_id} 不在屏蔽列表中")
            return
        
        self.blocked_groups.remove(group_id)
        self.save_blocked_groups()
        yield event.plain_result(f"已解除屏蔽群组 {group_id}")
    
    @filter.command("list_blocked_groups", permission_type=filter.PermissionType.ADMIN)
    async def list_blocked_groups(self, event: AstrMessageEvent):
        """列出所有被屏蔽的群组"""
        if not self.blocked_groups:
            yield event.plain_result("当前没有群组被屏蔽")
            return
        
        groups_list = "\n".join(self.blocked_groups)
        yield event.plain_result(f"被屏蔽的群组:\n{groups_list}")
    
    @filter.on_llm_request()
    async def check_blocked_group(self, event: AstrMessageEvent, req):
        """检查群组是否被屏蔽"""
        group_id = event.get_group_id()
        if group_id and group_id in self.blocked_groups:
            # 阻止LLM请求
            yield event.plain_result("此群组已被屏蔽，无法使用LLM功能")
            event.stop_event()
    
    async def terminate(self):
        """插件卸载时保存数据"""
        self.save_blocked_groups()
