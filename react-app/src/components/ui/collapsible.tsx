import * as React from "react";
import { cn } from "@/lib/utils";

const Collapsible = React.forwardRef<
  HTMLDivElement,
  {
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
    children: React.ReactNode;
    className?: string;
  }
>(({ open, onOpenChange, children, className, ...props }, ref) => {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const isOpen = open !== undefined ? open : internalOpen;

  const handleOpenChange = (newOpen: boolean) => {
    if (onOpenChange) {
      onOpenChange(newOpen);
    } else {
      setInternalOpen(newOpen);
    }
  };

  return (
    <div
      ref={ref}
      className={cn("", className)}
      data-state={isOpen ? "open" : "closed"}
      {...props}
      data-oid="2a-genv"
    >
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            ...child.props,
            "data-state": isOpen ? "open" : "closed",
            onToggle: () => handleOpenChange(!isOpen),
          } as any);
        }
        return child;
      })}
    </div>
  );
});
Collapsible.displayName = "Collapsible";

const CollapsibleTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    onToggle?: () => void;
  }
>(({ className, children, onToggle, ...props }, ref) => {
  return (
    <button
      ref={ref}
      className={cn(
        "flex w-full items-center justify-between py-4 font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180",
        className,
      )}
      onClick={onToggle}
      {...props}
      data-oid="3tm_f62"
    >
      {children}
    </button>
  );
});
CollapsibleTrigger.displayName = "CollapsibleTrigger";

const CollapsibleContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    "data-state"?: string;
  }
>(({ className, children, ...props }, ref) => {
  const dataState = props["data-state"];
  const isOpen = dataState === "open";

  return (
    <div
      ref={ref}
      className={cn(
        "overflow-hidden transition-all duration-200 ease-in-out",
        className,
      )}
      style={{
        display: isOpen ? "block" : "none",
      }}
      {...props}
      data-oid="p3eetyb"
    >
      <div className="pb-4 pt-0" data-oid="mmu5squ">
        {children}
      </div>
    </div>
  );
});
CollapsibleContent.displayName = "CollapsibleContent";

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
