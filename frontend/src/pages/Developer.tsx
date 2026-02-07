import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { usePageTracking } from '@/hooks/usePageTracking';

const Developer = () => {
  usePageTracking('developer');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [imageUrl, setImageUrl] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    supabase.from('learn_blocks').insert({ title, body_md: body, image_url: imageUrl });
    setTitle(''); setBody(''); setImageUrl('');
  };

  return (
    <div className="min-h-screen relative">
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-6">Add Learn Content</h1>
        <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
          <CardContent className="p-6">
            <form className="space-y-4" onSubmit={submit}>
              <Input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" />
              <Textarea placeholder="Markdown or code" value={body} onChange={e => setBody(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white min-h-40" />
              <Input placeholder="Image URL (optional)" value={imageUrl} onChange={e => setImageUrl(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" />
              <Button type="submit" className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">Publish</Button>
            </form>
          </CardContent>
        </Card>
      </div>
      <Footer />
    </div>
  );
};

export default Developer;


