import { features } from "@/lib/data";

export default function Features() {
  return (
     <section className="container py-16 mx-auto" id="features">
     <div className="mx-auto max-w-5xl space-y-12">
       <div className="text-center">
         <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">Powerful Features</h2>
         <p className="text-gray-500 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed dark:text-gray-400">Everything you need to transform your long-form content into engaging short clips</p>
       </div>
       <div className="grid gap-8 md:grid-cols-3">
         {features.map((feature) => (
           <div key={feature.title} className="space-y-4 rounded-lg border p-6">
             <div className="inline-flex rounded-lg bg-primary/10 p-2 text-primary">
               <feature.icon className="h-5 w-5" />
             </div>
             <h3 className="text-xl font-bold">{feature.title}</h3>
             <p className="text-muted-foreground">{feature.description}</p>
           </div>
         ))}
       </div>
     </div>
   </section>
  )
}