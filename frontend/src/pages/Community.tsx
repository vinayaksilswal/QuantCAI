import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { usePageTracking } from '@/hooks/usePageTracking';
import { api } from '@/lib/api';

const Community = () => {
  usePageTracking('community');
  const { user, role } = useAuth();
  const [posts, setPosts] = useState<any[]>([]);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);
  
  const load = async () => {
    try {
      setLoading(true);
      const data = await api.getPosts();
      setPosts(data ?? []);
    } catch (error) {
      console.error('Error loading posts:', error);
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { load(); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !title.trim() || !body.trim()) return;
    try {
      await api.createPost(title, body, user.id);
      setTitle('');
      setBody('');
      load();
    } catch (error) {
      console.error('Error creating post:', error);
    }
  };

  const addComment = async (postId: string, commentBody: string) => {
    if (!user || !commentBody.trim()) return;
    try {
      await api.createComment(parseInt(postId), commentBody, user.id);
      load();
    } catch (error) {
      console.error('Error creating comment:', error);
    }
  };

  const toggleLike = async (postId: string) => {
    if (!user) return;
    try {
      await api.toggleLike(parseInt(postId), user.id);
      load();
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  };

  const canModerate = (authorId: string | null | undefined) => {
    if (!user) return false;
    if (role === 'root' || role === 'developer') return true;
    return authorId === user.id.toString();
  };

  const deletePost = async (postId: string) => {
    if (!user) return;
    try {
      await api.deletePost(parseInt(postId));
      load();
    } catch (error) {
      console.error('Error deleting post:', error);
    }
  };

  const deleteComment = async (commentId: string) => {
    if (!user) return;
    try {
      await api.deleteComment(parseInt(commentId));
      load();
    } catch (error) {
      console.error('Error deleting comment:', error);
    }
  };

  return (
    <div className="min-h-screen relative">
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-6">Community</h1>
        {user && (
          <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm mb-6">
            <CardContent className="p-6 text-gray-300">
              <form onSubmit={submit} className="space-y-3">
                <Input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" />
                <Textarea placeholder="Share with the community" value={body} onChange={e => setBody(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" />
                <Button type="submit" className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">Post</Button>
              </form>
            </CardContent>
          </Card>
        )}

        {loading && (
          <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm mb-6">
            <CardContent className="p-6">
              <p className="text-gray-300">Loading posts...</p>
            </CardContent>
          </Card>
        )}
        {!loading && posts.length === 0 && (
          <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm mb-6">
            <CardContent className="p-6">
              <p className="text-gray-300">No posts yet. Be the first to share something!</p>
            </CardContent>
          </Card>
        )}
        {posts.map(p => {
          const likeCount = p.likes?.length ?? 0;
          const commentCount = p.comments?.length ?? 0;
          const likedByMe = (p.likes ?? []).some((l: any) => l.user_id === user?.id?.toString());
          return (
          <Card key={p.id} className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm mb-4">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-xl font-semibold text-white">{p.title}</h3>
                {canModerate(p.author?.id) && (
                  <button onClick={() => deletePost(p.id)} className="text-red-300 hover:text-red-400 text-sm">🗑️ Delete</button>
                )}
              </div>
              <p className="text-gray-400 text-sm mb-2">by {p.author?.email ?? 'Unknown'}</p>
              <p className="text-gray-300 whitespace-pre-wrap mb-4">{p.body}</p>
              <div className="flex items-center gap-4 text-gray-300">
                <button onClick={() => toggleLike(p.id)} className="hover:text-white flex items-center gap-1">
                  {likedByMe ? '❤️' : '🤍'} {likeCount}
                </button>
                <span className="flex items-center gap-1">💬 {commentCount}</span>
              </div>
              {user && (
                <div className="mt-3 flex gap-2">
                  <Input placeholder="Write a comment" className="bg-slate-800/50 border-slate-600 text-white" onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const target = e.target as HTMLInputElement;
                      addComment(p.id, target.value);
                      target.value = '';
                    }
                  }} />
                </div>
              )}
              {p.comments && p.comments.length > 0 && (
                <div className="mt-4 space-y-2">
                  {p.comments.map((c: any) => (
                    <div key={c.id} className="bg-slate-800/40 border border-slate-700 rounded p-2 text-gray-300 flex justify-between gap-2">
                      <div className="flex-1">
                        <div className="text-sm text-white font-medium">{c.author?.email ?? 'Unknown'}</div>
                        <div className="whitespace-pre-wrap">{c.body}</div>
                      </div>
                      {canModerate(c.author?.id) && (
                        <button onClick={() => deleteComment(c.id)} className="text-red-300 hover:text-red-400 text-sm">Delete</button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        );})}
      </div>
      <Footer />
    </div>
  );
};

export default Community;


