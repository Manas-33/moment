import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";

export default function FAQ() {
    return (
        <section className="bg-secondary w-full py-12 md:py-24 lg:py-24 flex flex-col items-center justify-center relative">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 -right-16 w-32 h-32 bg-primary-light rounded-full"
          animate={{
            y: [0, -20, 0],
            x: [0, 20, 0],
          }}
          transition={{
            duration: 5,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-1/4 -left-16 w-24 h-24 bg-secondary-light rounded-full"
          animate={{
            y: [0, 30, 0],
            x: [0, -30, 0],
          }}
          transition={{
            duration: 7,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
      </div>
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">Frequently Asked Questions</h2>
                <p className="text-gray-500 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed dark:text-gray-400">
                  Got questions? We&apos;ve got answers.
                </p>
              </div>
            </div>
            <div className="mx-auto max-w-3xl space-y-4 py-12">
              <div className="rounded-lg border border-secondary-foreground p-4">
                <button className="flex w-full items-center justify-between">
                  <span className="font-semibold">What file formats do you support?</span>
                  <ChevronDown className="h-5 w-5" />
                </button>
                <div className="mt-2 text-muted-foreground">
                  We support most common audio and video formats including MP3, WAV, MP4, and MOV.
                </div>
              </div>
              <div className="rounded-lg border border-secondary-foreground p-4">
                <button className="flex w-full items-center justify-between">
                  <span className="font-semibold">How long does it take to process a video?</span>
                  <ChevronDown className="h-5 w-5" />
                </button>
                <div className="mt-2 text-muted-foreground">
                  Processing time varies based on the length of your content, but typically takes 5-10 minutes for a
                  1-hour podcast.
                </div>
              </div>
              <div className="rounded-lg border border-secondary-foreground p-4">
                <button className="flex w-full items-center justify-between">
                  <span className="font-semibold">Which languages do you support?</span>
                  <ChevronDown className="h-5 w-5" />
                </button>
                <div className="mt-2 text-muted-foreground">
                  We support over 30 languages including English, Spanish, French, German, Chinese, and Japanese.
                </div>
              </div>
            </div>
          </div>
        </section>
    );
}