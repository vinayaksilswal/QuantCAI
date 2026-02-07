import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { api } from '@/lib/api';

interface NewsletterFormProps {
  compact?: boolean;
}

export const NewsletterForm = ({ compact = false }: NewsletterFormProps) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    setLoading(true);
    try {
      const result = await api.subscribe(email);
      toast({
        title: "Thank you for subscribing!",
        description: result.message || "You'll receive our latest quantum computing insights.",
      });
      setEmail('');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to subscribe. Please try again.';
      toast({
        title: "Subscription failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (compact) {
    return (
      <form onSubmit={handleSubmit} className="space-y-3">
        <Input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="bg-blue-800/50 border-blue-600 text-white placeholder-blue-300"
          required
        />
        <Button 
          type="submit" 
          className="w-full bg-white text-blue-700 hover:bg-blue-50"
          disabled={loading}
        >
          {loading ? 'Subscribing...' : 'Subscribe'}
        </Button>
      </form>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto">
      <div className="flex gap-4">
        <Input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1 bg-white/10 border-white/30 text-white placeholder-blue-300"
          required
        />
        <Button 
          type="submit" 
          className="bg-white text-blue-700 hover:bg-blue-50 px-8"
          disabled={loading}
        >
          {loading ? 'Subscribing...' : 'Subscribe'}
        </Button>
      </div>
    </form>
  );
};
