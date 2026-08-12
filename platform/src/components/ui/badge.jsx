import { cva } from "class-variance-authority"; import { cn } from "../../lib/utils";
const variants=cva("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",{variants:{variant:{default:"border-transparent bg-primary text-primary-foreground",secondary:"border-transparent bg-secondary text-secondary-foreground",outline:"text-foreground",draft:"border-amber-200 bg-amber-50 text-amber-900"}},defaultVariants:{variant:"default"}});
export function Badge({className,variant,...props}){return <div className={cn(variants({variant}),className)} {...props}/>}
