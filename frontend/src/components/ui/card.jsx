import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

const Card        = forwardRef(({ className, ...props }, ref) => <div ref={ref} className={cn('rounded-lg border bg-card text-card-foreground shadow-sm', className)} {...props} />)
const CardHeader  = forwardRef(({ className, ...props }, ref) => <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />)
const CardTitle       = forwardRef(({ className, ...props }, ref) => <h2 ref={ref} className={cn('font-semibold leading-none tracking-tight', className)} {...props} />)
const CardDescription = forwardRef(({ className, ...props }, ref) => <p ref={ref} className={cn('text-sm text-muted-foreground', className)} {...props} />)
const CardContent     = forwardRef(({ className, ...props }, ref) => <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />)

Card.displayName = 'Card'
CardHeader.displayName = 'CardHeader'
CardTitle.displayName = 'CardTitle'
CardDescription.displayName = 'CardDescription'
CardContent.displayName = 'CardContent'

export { Card, CardHeader, CardTitle, CardDescription, CardContent }
