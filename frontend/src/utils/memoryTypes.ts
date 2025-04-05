// 记忆类型枚举
export enum MemoryType {
  RAW = "raw",
  INSIGHT = "insight",
  PROJECT = "project",
  TASK = "task",
  DIARY = "diary", 
  WEEKLY = "weekly",
  MONTHLY = "monthly",
  QUARTERLY = "quarterly",
  YEARLY = "yearly",
  ARCHIVED = "archived",
}

// 记忆类型中文名称
export const MemoryTypeNames: Record<string, string> = {
  [MemoryType.RAW]: "原始记忆",
  [MemoryType.INSIGHT]: "洞察记忆",
  [MemoryType.PROJECT]: "项目记忆",
  [MemoryType.TASK]: "项目任务",
  [MemoryType.DIARY]: "日记",
  [MemoryType.WEEKLY]: "周报",
  [MemoryType.MONTHLY]: "月报",
  [MemoryType.QUARTERLY]: "季报",
  [MemoryType.YEARLY]: "年报",
  [MemoryType.ARCHIVED]: "已归档",
  "all": "全部",
};

// 获取记忆类型选项列表，用于下拉菜单
export const getMemoryTypeOptions = () => {
  const options = [
    { value: "all", label: MemoryTypeNames["all"] },
  ];
  
  Object.values(MemoryType).forEach(type => {
    options.push({
      value: type,
      label: MemoryTypeNames[type] || type
    });
  });
  
  return options;
};