"use client"

import * as React from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import {
  Captions,
  Crop,
  Link as LinkIcon,
  Loader2,
  Minus,
  Plus,
  Scissors,
  Sparkles,
  Upload,
  Youtube,
  type LucideIcon,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"

const youtubeUrlSchema = z.object({
  youtubeUrl: z
    .string()
    .min(1, { message: "YouTube URL is required" })
    .url({ message: "Please enter a valid URL" })
    .refine(
      (url) => {
        return (
          url.includes("youtube.com/watch") ||
          url.includes("youtu.be/") ||
          url.includes("youtube.com/v/") ||
          url.includes("youtube.com/embed/")
        )
      },
      { message: "Please enter a valid YouTube URL" },
    ),
  addCaptions: z.boolean().default(true),
  cropToPortrait: z.boolean().default(true),
  numShorts: z.coerce.number().min(1, { message: "At least 1 short is required" }).max(10, { message: "Maximum 10 shorts allowed" }).default(1),
})

const fileUploadSchema = z.object({
  file: z
    .custom<FileList>(
      (val): val is FileList =>
        typeof FileList !== "undefined" && val instanceof FileList,
      { message: "Invalid file input" }
    )
    .refine((files) => files.length > 0, {
      message: "Please select a file",
    })
    .refine((files) => files[0].size <= 20 * 1024 * 1024, {
      message: "File size must be less than 20MB",
    })
    .refine((files) => {
      const file = files[0];
      return ["video/mp4", "video/avi", "video/quicktime"].includes(file.type);
    }, {
      message: "File must be in MP4, AVI, or MOV format",
    }),

  addCaptions: z.boolean().default(true),
  cropToPortrait: z.boolean().default(true),

  numShorts: z.coerce
    .number()
    .min(1, { message: "At least 1 short is required" })
    .max(10, { message: "Maximum 10 shorts allowed" })
    .default(1),
});

interface PodcastFormProps {
  onSubmit: (url: string, isYoutubeUrl: boolean, addCaptions: boolean, numShorts: number, cropToPortrait: boolean) => Promise<void>;
  isLoading: boolean;
}

function SettingRow({
  icon: Icon,
  title,
  description,
  children,
  last,
}: {
  icon: LucideIcon
  title: string
  description: string
  children: React.ReactNode
  last?: boolean
}) {
  return (
    <div className={cn("flex items-center gap-4 py-[18px]", !last && "border-b border-border/70")}>
      <div className="flex size-10 flex-none items-center justify-center rounded-xl bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1">
        <div className="text-sm font-semibold text-foreground">{title}</div>
        <div className="mt-0.5 text-[13px] leading-snug text-muted-foreground">{description}</div>
      </div>
      {children}
    </div>
  )
}

function Stepper({ value, onChange }: { value: number; onChange: (n: number) => void }) {
  return (
    <div className="flex items-center gap-1 rounded-xl border border-input bg-card p-1">
      <button
        type="button"
        aria-label="Decrease"
        onClick={() => onChange(Math.max(1, (value || 1) - 1))}
        className="flex size-8 items-center justify-center rounded-lg bg-muted text-muted-foreground transition-colors hover:bg-secondary"
      >
        <Minus className="h-4 w-4" />
      </button>
      <div className="w-[42px] text-center font-display text-base font-bold text-foreground">{value}</div>
      <button
        type="button"
        aria-label="Increase"
        onClick={() => onChange(Math.min(10, (value || 1) + 1))}
        className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors hover:bg-primary/20"
      >
        <Plus className="h-4 w-4" />
      </button>
    </div>
  )
}

export function PodcastForm({ onSubmit, isLoading }: PodcastFormProps) {
  const [activeTab, setActiveTab] = React.useState("youtube")

  const youtubeForm = useForm<z.infer<typeof youtubeUrlSchema>>({
    resolver: zodResolver(youtubeUrlSchema),
    defaultValues: {
      youtubeUrl: "",
      addCaptions: true,
      cropToPortrait: true,
      numShorts: 4,
    },
  })

  const fileForm = useForm<z.infer<typeof fileUploadSchema>>({
    resolver: zodResolver(fileUploadSchema),
    defaultValues: {
      addCaptions: true,
      cropToPortrait: true,
      numShorts: 4,
    },
  })

  async function onYoutubeSubmit(values: z.infer<typeof youtubeUrlSchema>) {
    await onSubmit(values.youtubeUrl, true, values.addCaptions, values.numShorts, values.cropToPortrait);
  }

  async function onFileSubmit(values: z.infer<typeof fileUploadSchema>) {
    const fileURL = URL.createObjectURL(values.file[0]);
    await onSubmit(fileURL, false, values.addCaptions, values.numShorts, values.cropToPortrait);
  }

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-[0_1px_2px_rgba(30,27,23,0.04),0_12px_30px_-20px_rgba(30,27,23,0.14)] sm:p-7">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="h-11 w-fit gap-1 rounded-xl p-1">
          <TabsTrigger value="youtube" className="gap-2 rounded-lg px-4 text-[13px]">
            <Youtube className="h-[17px] w-[17px] text-primary" />
            YouTube URL
          </TabsTrigger>
          <TabsTrigger value="upload" className="gap-2 rounded-lg px-4 text-[13px]">
            <Upload className="h-[17px] w-[17px]" />
            Upload file
          </TabsTrigger>
        </TabsList>

        {/* YOUTUBE */}
        <TabsContent value="youtube" className="mt-0">
          <Form {...youtubeForm}>
            <form onSubmit={youtubeForm.handleSubmit(onYoutubeSubmit)} className="space-y-5">
              <FormField
                control={youtubeForm.control}
                name="youtubeUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <div className="flex gap-2.5">
                        <div className="relative flex flex-1 items-center">
                          <LinkIcon className="pointer-events-none absolute left-3.5 h-[18px] w-[18px] text-muted-foreground" />
                          <Input
                            placeholder="https://youtube.com/watch?v=…"
                            className="h-11 rounded-xl pl-11"
                            {...field}
                          />
                        </div>
                        <Button type="submit" disabled={isLoading} className="h-11 rounded-xl px-5">
                          {isLoading ? (
                            <>
                              <Loader2 className="h-[17px] w-[17px] animate-spin" />
                              Processing
                            </>
                          ) : (
                            <>
                              <Sparkles className="h-[17px] w-[17px]" />
                              Generate
                            </>
                          )}
                        </Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="border-t pt-1">
                <FormField
                  control={youtubeForm.control}
                  name="numShorts"
                  render={({ field }) => (
                    <SettingRow icon={Scissors} title="Number of shorts" description="Between 1 and 10 clips per batch.">
                      <Stepper value={field.value} onChange={field.onChange} />
                    </SettingRow>
                  )}
                />
                <FormField
                  control={youtubeForm.control}
                  name="addCaptions"
                  render={({ field }) => (
                    <SettingRow icon={Captions} title="Add captions" description="Word-level captions, highlighted as spoken.">
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </SettingRow>
                  )}
                />
                <FormField
                  control={youtubeForm.control}
                  name="cropToPortrait"
                  render={({ field }) => (
                    <SettingRow icon={Crop} title="Crop to portrait" description="Reframe to 9:16 and follow the active speaker." last>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </SettingRow>
                  )}
                />
              </div>
            </form>
          </Form>
        </TabsContent>

        {/* UPLOAD */}
        <TabsContent value="upload" className="mt-0">
          <Form {...fileForm}>
            <form onSubmit={fileForm.handleSubmit(onFileSubmit)} className="space-y-5">
              <FormField
                control={fileForm.control}
                name="file"
                render={({ field: { onChange, value, ...rest } }) => (
                  <FormItem>
                    <FormControl>
                      <div className="flex flex-col gap-2.5 sm:flex-row">
                        <Input
                          type="file"
                          accept=".mp4,.avi,.mov"
                          onChange={(e) => onChange(e.target.files)}
                          className="h-11 rounded-xl file:mr-3 file:text-primary"
                          {...rest}
                        />
                        <Button type="submit" disabled={isLoading} className="h-11 rounded-xl px-5">
                          {isLoading ? (
                            <>
                              <Loader2 className="h-[17px] w-[17px] animate-spin" />
                              Processing
                            </>
                          ) : (
                            <>
                              <Upload className="h-[17px] w-[17px]" />
                              Upload &amp; Generate
                            </>
                          )}
                        </Button>
                      </div>
                    </FormControl>
                    <p className="mt-2 text-[13px] text-muted-foreground">MP4, AVI or MOV, up to 20MB.</p>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="border-t pt-1">
                <FormField
                  control={fileForm.control}
                  name="numShorts"
                  render={({ field }) => (
                    <SettingRow icon={Scissors} title="Number of shorts" description="Between 1 and 10 clips per batch.">
                      <Stepper value={field.value} onChange={field.onChange} />
                    </SettingRow>
                  )}
                />
                <FormField
                  control={fileForm.control}
                  name="addCaptions"
                  render={({ field }) => (
                    <SettingRow icon={Captions} title="Add captions" description="Word-level captions, highlighted as spoken.">
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </SettingRow>
                  )}
                />
                <FormField
                  control={fileForm.control}
                  name="cropToPortrait"
                  render={({ field }) => (
                    <SettingRow icon={Crop} title="Crop to portrait" description="Reframe to 9:16 and follow the active speaker." last>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </SettingRow>
                  )}
                />
              </div>
            </form>
          </Form>
        </TabsContent>
      </Tabs>
    </div>
  )
}
