import * as TabsPrimitive from "@radix-ui/react-tabs"; import { cn } from "../../lib/utils";
export const Tabs=TabsPrimitive.Root;
export const TabsList=({className,...props})=><TabsPrimitive.List className={cn("inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",className)} {...props}/>;
export const TabsTrigger=({className,...props})=><TabsPrimitive.Trigger className={cn("inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",className)} {...props}/>;
export const TabsContent=({className,...props})=><TabsPrimitive.Content className={cn("mt-4 focus-visible:outline-none",className)} {...props}/>;
