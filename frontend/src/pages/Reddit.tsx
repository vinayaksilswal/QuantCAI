import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { usePageTracking } from '@/hooks/usePageTracking';

const Reddit = () => {
  usePageTracking('reddit');
  return (
    <div className="min-h-screen relative">
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-6">Reddit Community</h1>
        <div className="aspect-video w-full rounded-lg overflow-hidden border border-slate-700">
          <iframe
            title="Reddit Embed"
            src="https://www.reddit.com/r/QuantumComputing/"
            className="w-full h-full bg-white"
          />
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Reddit;


