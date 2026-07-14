import FloatingNav from '../components/FloatingNav'
import Hero from '../components/Hero'
import FeaturesSection from '../components/FeaturesSection'
import TechSection from '../components/TechSection'
import SecuritySection from '../components/SecuritySection'

export default function LandingPage() {
  return (
    <>
      <FloatingNav />
      <main className="space-y-12">
        <Hero />
        <FeaturesSection />
        <TechSection />
        <SecuritySection />
      </main>
    </>
  )
}
