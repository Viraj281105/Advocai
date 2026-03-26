import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import StatsBar from "@/components/StatsBar";
import HowItWorks from "@/components/HowItWorks";
import AgentCards from "@/components/AgentCards";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";
import PipelineDiagram from "@/components/PipelineDiagram";

export default function Home() {
  return (
    <main>
      <Navbar />
      <HeroSection />
      <StatsBar />
      <HowItWorks />
      <AgentCards />
      <PipelineDiagram />
      <CTASection />
      <Footer />
    </main>
  );
}