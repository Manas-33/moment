"use client"
import { API_URL } from "@/lib/api";

import React, { useEffect, useState, Suspense } from "react"
import { AppSidebar } from "@//components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@//components/ui/breadcrumb"
import { Separator } from "@//components/ui/separator"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@//components/ui/sidebar"
import { PodcastForm } from "@//components/podcast-form"
import { ReelsResults } from "@//components/reels-results"
import { useToast } from "@/components/ui/use-toast"
import Link from "next/link"
import { History, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { useSearchParams } from "next/navigation"

interface ProcessingData {
  id: string
  username: string
  youtube_url: string
  status: string
  cloudinary_url: string | null
  cloudinary_urls: Array<{ url: string, public_id: string }>
  num_shorts: number
  created_at: string
  updated_at: string
}

interface User {
  name: string
  email: string
  avatar: string
} 

interface ApiResponse {
  message: string
  processing: ProcessingData
}

// Local-mode constants: no auth, no Supabase. A single shared "local" user owns
// all generated content while running offline.
const LOCAL_USERNAME = "local"
const LOCAL_USER: User = {
  name: "Local User",
  email: LOCAL_USERNAME,
  avatar: "/placeholder.svg?height=32&width=32",
}

// Client component that handles URL parameters
function DashboardContent() {
  const [isLoading, setIsLoading] = useState(false)
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [processingStatus, setProcessingStatus] = useState<string | null>(null)
  const [username] = useState<string>(LOCAL_USERNAME)
  const [parsedUser] = useState<User>(LOCAL_USER)
  const [userVideos, setUserVideos] = useState<ProcessingData[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const { toast } = useToast()
  const searchParams = useSearchParams()
  const idFromUrl = searchParams.get('id')

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        if (idFromUrl) {
          await fetchProcessingById(idFromUrl);
        } else {
          await fetchUserVideos(LOCAL_USERNAME);
        }
      } catch (error) {
        console.error("Error loading dashboard data:", error);
        setIsLoadingHistory(false);
      }
    };

    loadInitialData();
  }, [idFromUrl]);

  // Function to fetch a specific processing by ID
  const fetchProcessingById = async (id: string) => {
    try {
      setIsLoadingHistory(true);
      const response = await fetch(`${API_URL}/api/shorts/status/${id}/`);
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'COMPLETED') {
          setApiResponse({
            message: "Retrieved video",
            processing: data
          });
        }
        
        // Also fetch all videos to keep the list updated
        if (username) {
          await fetchUserVideos(username);
        }
      } else {
        console.error("Failed to fetch processing by ID");
        toast({
          title: "Failed to load video",
          description: "Could not load the requested video",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching processing by ID:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };
  
  // Function to fetch user's videos
  const fetchUserVideos = async (userEmail: string) => {
    try {
      setIsLoadingHistory(true);
      const response = await fetch(`${API_URL}/api/shorts/user/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: userEmail }),
      });
      
      if (response.ok) {
        const videos = await response.json();
        setUserVideos(videos);
        
        // If there are completed videos, set the latest one as the current video
        // (only if we're not already loading a specific video by ID)
        if (!idFromUrl) {
          const completedVideos = videos.filter((video: ProcessingData) => video.status === 'COMPLETED');
          
          if (completedVideos.length > 0) {
            // Sort by updated_at to get the most recent one
            const latestVideo = completedVideos.sort((a: ProcessingData, b: ProcessingData) => 
              new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
            )[0];
            
            // Set the latest video as the current video
            setApiResponse({
              message: "Retrieved previous video",
              processing: latestVideo
            });
          }
        }
      } else {
        console.error("Failed to fetch user videos");
      }
    } catch (error) {
      console.error("Error fetching user videos:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Poll for status updates if we have a processing ID and status is not completed
  useEffect(() => {
    if (!processingId || processingStatus === 'COMPLETED' || processingStatus === 'FAILED') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/shorts/status/${processingId}/`);
        const data = await response.json();
        
        setProcessingStatus(data.status);
        
        // Update the API response with the latest data
        if (data.status === 'COMPLETED') {
          setApiResponse(prev => {
            if (!prev) return null;
            return {
              ...prev,
              processing: data
            };
          });
          
          // Update our list of user videos to include this new one
          setUserVideos(prevVideos => {
            const exists = prevVideos.some(video => video.id === data.id);
            if (exists) {
              return prevVideos.map(video => 
                video.id === data.id ? data : video
              );
            } else {
              return [data, ...prevVideos];
            }
          });
          
          setIsLoading(false);
          clearInterval(interval);
          
          toast({
            title: 'Processing completed',
            description: "We've generated shorts from your podcast",
          });
        } else if (data.status === 'FAILED') {
          setIsLoading(false);
          clearInterval(interval);
          
          toast({
            title: 'Processing failed',
            description: data.error_message || 'Please try again later',
            variant: 'destructive',
          });
        }
      } catch (error) {
        console.error('Error checking status:', error);
      }
    }, 5000); 

    return () => clearInterval(interval);
  }, [processingId, processingStatus, toast]);

  const handlePodcastSubmit = async (url: string, isYoutubeUrl: boolean, addCaptions: boolean, numShorts: number, cropToPortrait: boolean) => {
    setIsLoading(true)
    
    try {
      const response = await fetch(`${API_URL}/api/shorts/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          username: username,
          num_shorts: numShorts,
          add_captions: addCaptions,
          crop_to_portrait: cropToPortrait,
        }),
      })
  
      const data = await response.json()
      console.log('API Response:', data)
  
      if (response.ok) {
        setApiResponse(data)
        setProcessingId(data.processing.id)
        setProcessingStatus(data.processing.status)
        setUserVideos(prevVideos => [data.processing, ...prevVideos]);
        toast({
          title: 'Processing started',
          description: `Started processing ${data.processing.num_shorts} shorts from your podcast`,
        })
      } else {
        setIsLoading(false)
        toast({
          title: 'Something went wrong',
          description: data?.error || 'Please try again later',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('API Error:', error)
      setIsLoading(false)
      toast({
        title: 'Something went wrong',
        description: 'Please try again later',
        variant: 'destructive',
      })
    }
  }

  // Transform the backend API response format to the format expected by ReelsResults
  const transformedApiResponse = apiResponse && apiResponse.processing.status === 'COMPLETED' ? {
    message: apiResponse.message,
    video_path: apiResponse.processing.youtube_url,
    clips: apiResponse.processing.cloudinary_urls.map((item, index) => ({
      clip_number: index + 1,
      url: item.url
    }))
  } : null;

  return (
    <SidebarProvider>
      <AppSidebar user={parsedUser}/>
      <SidebarInset>
        <header className="flex h-[66px] shrink-0 items-center gap-2 border-b bg-card/60 px-5">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-1 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink href="/dashboard">Studio</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="hidden md:block" />
              <BreadcrumbItem>
                <BreadcrumbPage>Create</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <div className="ml-auto flex items-center gap-2.5">
            <Button variant="outline" size="sm" asChild>
              <Link href="/dashboard/history">
                <History className="mr-1.5 h-4 w-4" />
                View history
              </Link>
            </Button>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-8 p-8 md:p-11">
          <div className="mx-auto w-full max-w-3xl">
            <div className="mb-8">
              <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">
                Create shorts from any video
              </h1>
              <p className="mt-2.5 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
                Paste a YouTube link or upload a file. Moment transcribes it, finds the
                strongest moments, and cuts them into vertical shorts.
              </p>
            </div>
            <PodcastForm onSubmit={handlePodcastSubmit} isLoading={isLoading} />
            {isLoadingHistory ? (
              <div className="mt-6 text-center">
                <p>Loading your videos...</p>
              </div>
            ) : (
              <>
                {processingStatus && processingStatus !== 'COMPLETED' && isLoading && (
                  <div className="mt-6 text-center">
                    <p className="text-lg font-medium">Processing your podcast...</p>
                    <p className="text-sm text-muted-foreground">Status: {processingStatus}</p>
                  </div>
                )}
                {transformedApiResponse && (
                  <div className="mt-6">
                    <ReelsResults apiResponse={transformedApiResponse} />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

// Main page component with Suspense boundary
export default function Page() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  )
}