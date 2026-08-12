import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const variants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50", { variants: { variant: { default: "bg-primary text-primary-foreground hover:bg-primary/90", destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90", outline: "border border-input bg-background hover:bg-accent", ghost: "hover:bg-accent", secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80" }, size: { default: "h-10 px-4 py-2", sm: "h-9 rounded-md px-3", icon: "h-10 w-10" } }, defaultVariants: { variant: "default", size: "default" } });
export const Button = React.forwardRef(({ className, variant, size, asChild=false, ...props }, ref) => { const Comp=asChild?Slot:"button"; return <Comp ref={ref} className={cn(variants({variant,size}),className)} {...props}/>; });
Button.displayName="Button";
