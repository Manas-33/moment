import { LandingNav, LandingFooter } from "@/components/landing"
import Pricing from "@/components/Pricing"

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNav active="pricing" />
      <Pricing />
      <LandingFooter />
    </div>
  )
}
