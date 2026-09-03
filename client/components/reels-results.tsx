"use client"

import * as React from "react"
import { Play, Share2, Download, Pause, Volume2, VolumeX, Languages, CheckCircle2 } from "lucide-react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/use-toast"
import { Slider } from "@/components/ui/slider"

interface Clip {
  clip_number: number
  url: string
}

interface ApiResponse {
  message: string
  video_path: string
  clips: Clip[]
}

interface ReelsResultsProps {
  apiResponse: ApiResponse | null
}

export function ReelsResults({ apiResponse }: ReelsResultsProps) {
  const [currentPlayingIndex, setCurrentPlayingIndex] = React.useState<number | null>(null)
  const [hoveredIndex, setHoveredIndex] = React.useState<number | null>(null)
  const [videoDurations, setVideoDurations] = React.useState<number[]>([])
  const [currentTimes, setCurrentTimes] = React.useState<number[]>([])
  const [isMuted, setIsMuted] = React.useState<boolean[]>([])
  const videoRefs = React.useRef<(HTMLVideoElement | null)[]>([])
  const { toast } = useToast()
  const router = useRouter()

  // Initialize state arrays when clips change
  React.useEffect(() => {
    if (apiResponse?.clips) {
      setVideoDurations(new Array(apiResponse.clips.length).fill(0))
      setCurrentTimes(new Array(apiResponse.clips.length).fill(0))
      setIsMuted(new Array(apiResponse.clips.length).fill(false))
    }
  }, [apiResponse?.clips])

  // Update current time during playback
  const handleTimeUpdate = (index: number) => {
    const video = videoRefs.current[index]
    if (video) {
      setCurrentTimes(prev => {
        const updated = [...prev]
        updated[index] = video.currentTime
        return updated
      })
    }
  }

  // Get video duration when loaded
  const handleLoadedMetadata = (index: number) => {
    const video = videoRefs.current[index]
    if (video) {
      setVideoDurations(prev => {
        const updated = [...prev]
        updated[index] = video.duration
        return updated
      })
    }
  }

  // Function to handle play button click
  const handlePlay = (index: number) => {
    // Pause any currently playing video
    if (currentPlayingIndex !== null && currentPlayingIndex !== index) {
      const currentVideo = videoRefs.current[currentPlayingIndex]
      if (currentVideo) {
        currentVideo.pause()
      }
    }

    // Play the selected video
    const video = videoRefs.current[index]
    if (video) {
      if (video.paused) {
        video.play()
          .then(() => {
            setCurrentPlayingIndex(index)
          })
          .catch(error => {
            console.error("Error playing video:", error)
            toast({
              title: "Playback error",
              description: "Could not play this video. Try again.",
              variant: "destructive"
            })
          })
      } else {
        video.pause()
        setCurrentPlayingIndex(null)
      }
    }
  }

  // Function to handle download
  const handleDownload = (url: string, clipNumber: number) => {
    const a = document.createElement('a')
    a.href = url
    a.download = `clip-${clipNumber}.mp4`
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    setTimeout(() => {
      document.body.removeChild(a)
    }, 100)
    toast({
      title: "Download started",
      description: `Clip ${clipNumber} is being downloaded`,
    })
  }

  const handleDownloadAll = () => {
    if (!apiResponse?.clips) return
    apiResponse.clips.forEach((clip, i) => {
      setTimeout(() => handleDownload(clip.url, clip.clip_number), i * 250)
    })
  }

  // Function to handle translation
  const handleTranslate = (url: string) => {
    router.push(`/translate?videoUrl=${encodeURIComponent(url)}`);
    toast({
      title: "Opening translator",
      description: "Redirecting to the translation page",
    });
  }

  // Handle seek in progress bar
  const handleSeek = (index: number, value: number[]) => {
    const video = videoRefs.current[index]
    if (video) {
      video.currentTime = value[0]
    }
  }

  // Toggle mute for a specific video
  const toggleMute = (index: number) => {
    const video = videoRefs.current[index]
    if (video) {
      const newMutedState = !video.muted
      video.muted = newMutedState
      setIsMuted(prev => {
        const updated = [...prev]
        updated[index] = newMutedState
        return updated
      })
    }
  }

  // Format time for display (MM:SS)
  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`
  }

  if (!apiResponse || !apiResponse.clips || apiResponse.clips.length === 0) return null

  // Set up videoRefs array based on clips length
  if (videoRefs.current.length !== apiResponse.clips.length) {
    videoRefs.current = Array(apiResponse.clips.length).fill(null)
  }

  return (
    <div id="results-section" className="mt-10">
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-display text-2xl font-bold tracking-tight text-foreground">
              Generated shorts
            </h2>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 font-mono text-xs font-semibold text-primary">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {apiResponse.clips.length} shorts generated
            </span>
          </div>
          <p className="mt-2 text-[15px] text-muted-foreground">
            Captions on &middot; reframed to 9:16 &middot; ready to post
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleDownloadAll}>
          <Download className="mr-1.5 h-4 w-4" />
          Download all
        </Button>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {apiResponse.clips.map((clip, index) => (
          <div
            key={`clip-${clip.clip_number}`}
            className="overflow-hidden rounded-2xl border bg-card shadow-[0_1px_2px_rgba(30,27,23,0.04),0_10px_24px_-18px_rgba(30,27,23,0.16)] transition-all hover:-translate-y-1 hover:shadow-[0_16px_34px_-20px_rgba(30,27,23,0.28)]"
          >
            <div
              className="relative aspect-[9/16] bg-muted"
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <video
                ref={(el) => {
                  videoRefs.current[index] = el;
                }}
                src={clip.url}
                className="h-full w-full cursor-pointer object-cover"
                onEnded={() => setCurrentPlayingIndex(null)}
                onTimeUpdate={() => handleTimeUpdate(index)}
                onLoadedMetadata={() => handleLoadedMetadata(index)}
                playsInline
                onClick={() => handlePlay(index)}
              />

              {/* label */}
              <span className="pointer-events-none absolute left-3 top-3 font-mono text-[10px] uppercase tracking-wider text-white/70">
                9:16
              </span>

              {/* duration chip */}
              {videoDurations[index] > 0 && (
                <span className="pointer-events-none absolute right-3 top-3 rounded-md bg-black/55 px-2 py-1 font-mono text-xs text-white backdrop-blur-sm">
                  {formatTime(videoDurations[index])}
                </span>
              )}

              {/* Play overlay button - only show when not playing */}
              {currentPlayingIndex !== index && (
                <div
                  className="absolute inset-0 flex items-center justify-center bg-black/15"
                  onClick={(e) => {
                    e.stopPropagation()
                    handlePlay(index)
                  }}
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/95 shadow-[0_8px_24px_-6px_rgba(0,0,0,0.5)] transition-transform hover:scale-105">
                    <Play className="ml-0.5 h-6 w-6 fill-primary text-primary" />
                  </div>
                </div>
              )}

              {/* Video controls - show when hovered or playing */}
              {(hoveredIndex === index || currentPlayingIndex === index) && (
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                  <div className="flex flex-col gap-2">
                    <Slider
                      value={[currentTimes[index] || 0]}
                      max={videoDurations[index] || 100}
                      step={0.1}
                      onValueChange={(values) => handleSeek(index, values)}
                      className="h-1"
                    />
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 rounded-full text-white hover:bg-white/20 hover:text-white"
                          onClick={(e) => {
                            e.stopPropagation()
                            handlePlay(index)
                          }}
                        >
                          {currentPlayingIndex === index ? (
                            <Pause className="h-4 w-4" />
                          ) : (
                            <Play className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 rounded-full text-white hover:bg-white/20 hover:text-white"
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleMute(index)
                          }}
                        >
                          {isMuted[index] ? (
                            <VolumeX className="h-4 w-4" />
                          ) : (
                            <Volume2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                      <span className="font-mono text-xs text-white">
                        {formatTime(currentTimes[index] || 0)} / {formatTime(videoDurations[index] || 0)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[15px] font-semibold text-foreground">Clip {clip.clip_number}</span>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-[34px] w-[34px] rounded-lg"
                  onClick={() => {
                    navigator.clipboard.writeText(clip.url)
                    toast({
                      title: "Link copied",
                      description: "Video link copied to clipboard",
                    })
                  }}
                >
                  <Share2 className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex gap-2.5">
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={(e) => {
                    e.preventDefault()
                    handleDownload(clip.url, clip.clip_number)
                  }}
                >
                  <Download className="mr-1.5 h-4 w-4" />
                  Download
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={(e) => {
                    e.preventDefault()
                    handleTranslate(clip.url)
                  }}
                >
                  <Languages className="mr-1.5 h-4 w-4" />
                  Translate
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
