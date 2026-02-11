
import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { Mail, Cpu, Mic, Workflow } from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Soon = () => {
  const [formData, setFormData] = useState({
    email: '',
    message: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/notify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.email, message: formData.message })
      });
      if (!res.ok) {
        throw new Error("Failed to submit");
      }
      toast({
        title: "Message sent!",
        description: "Thank you for contacting us. We'll keep you posted.",
      });
      setFormData({ email: '', message: '' });
    } catch (error) {
      toast({
        title: "Submission failed",
        description: "Please try again in a moment.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  usePageTracking('soon');
  return (
    <div className="min-h-screen relative">
      <Navbar />

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Coming <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Soon</span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Here's a preview of the features we're actively building.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* Upcoming Features */}
            <div className="space-y-6">
              <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm">
                <CardContent className="p-8">
                  <div className="flex items-center gap-3 mb-3">
                    <Mic className="h-6 w-6 text-blue-400" />
                    <h2 className="text-2xl font-bold text-white">AI Voice Bot</h2>
                  </div>
                  <ul className="text-gray-300 space-y-2 list-disc pl-5">
                    <li>Ask questions on any page and get spoken answers</li>
                    <li>Context-aware help for simulators and learning modules</li>
                    <li>Multilingual support</li>
                  </ul>
                  <div className="mt-4 text-sm text-blue-300">Status: In progress</div>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm">
                <CardContent className="p-8">
                  <div className="flex items-center gap-3 mb-3">
                    <Cpu className="h-6 w-6 text-purple-400" />
                    <h2 className="text-2xl font-bold text-white">Multi-Qubit Circuit Builder</h2>
                  </div>
                  <ul className="text-gray-300 space-y-2 list-disc pl-5">
                    <li>Design multiple circuits side-by-side</li>
                    <li>Gate library with drag-and-drop</li>
                    <li>Statevector and measurement visualization</li>
                  </ul>
                  <div className="mt-4 text-sm text-purple-300">Status: In design</div>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <Workflow className="h-5 w-5 text-green-400" />
                    <h3 className="text-xl font-bold text-white">Roadmap</h3>
                  </div>
                  <ol className="text-gray-300 list-decimal pl-5 space-y-1">
                    <li>Auth + progress tracking improvements</li>
                    <li>Community interactions and moderation</li>
                    <li>Voice Bot beta</li>
                    <li>Multi-Qubit Circuit alpha</li>
                  </ol>
                </CardContent>
              </Card>
            </div>

            {/* Contact */}
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm h-min">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold text-white mb-4">Stay in the loop</h3>
                <p className="text-gray-300 leading-relaxed mb-4">
                  Want early access or to collaborate? Drop your message and we'll keep you posted.
                </p>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <Input id="email" name="email" type="email" value={formData.email} onChange={handleChange} className="bg-slate-800/50 border-slate-600 text-white" placeholder="your@email.com" required />
                  <Textarea id="message" name="message" value={formData.message} onChange={handleChange} className="bg-slate-800/50 border-slate-600 text-white min-h-32" placeholder="Tell us what you'd like to see..." required />
                  <Button type="submit" className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white">Notify Me</Button>
                </form>
                <div className="mt-4 flex items-center text-gray-300">
                  <Mail className="h-5 w-5 text-blue-400 mr-3" />
                  <a href="mailto:quantc.info@gmail.com" className="hover:text-blue-400 transition-colors">quantc.info@gmail.com</a>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Soon;
