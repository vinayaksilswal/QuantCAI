import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { usePageTracking } from '@/hooks/usePageTracking';
import { api } from '@/lib/api';
import { Heart, MessageSquare, Trash2, Send, PlusCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const Community = () => {
  usePageTracking('community');
  const { user, role } = useAuth();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [showCreatePost, setShowCreatePost] = useState(false);

  // Fetch posts using react-query
  const { data: posts = [], isLoading: loading } = useQuery({
    queryKey: ['posts'],
    queryFn: () => api.getPosts(),
  });

  // Mutations
  const createPostMutation = useMutation({
    mutationFn: ({ title, body }: { title: string, body: string }) =>
      api.createPost(title, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
      setTitle('');
      setBody('');
      setShowCreatePost(false);
      toast.success('Post created successfully!');
    },
    onError: (error: any) => {
      toast.error('Failed to create post: ' + error.message);
    }
  });

  const addCommentMutation = useMutation({
    mutationFn: ({ postId, body }: { postId: number, body: string }) =>
      api.createComment(postId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
      toast.success('Comment added!');
    }
  });

  const toggleLikeMutation = useMutation({
    mutationFn: ({ postId }: { postId: number }) =>
      api.toggleLike(postId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    }
  });

  const deletePostMutation = useMutation({
    mutationFn: (postId: number) => api.deletePost(postId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
      toast.success('Post deleted');
    }
  });

  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: number) => api.deleteComment(commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
      toast.success('Comment deleted');
    }
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !title.trim() || !body.trim()) return;
    createPostMutation.mutate({ title, body });
  };

  const addComment = async (postId: number, commentBody: string) => {
    if (!user || !commentBody.trim()) return;
    addCommentMutation.mutate({ postId, body: commentBody });
  };

  const toggleLike = async (postId: number) => {
    if (!user) return;
    toggleLikeMutation.mutate({ postId });
  };

  const canModerate = (authorId: string | null | undefined) => {
    if (!user) return false;
    if (role === 'root' || role === 'developer') return true;
    return authorId === user.id.toString();
  };

  const deletePost = async (postId: number) => {
    if (!user) return;
    if (window.confirm("Are you sure you want to delete this post?")) {
      deletePostMutation.mutate(postId);
    }
  };

  const deleteComment = async (commentId: number) => {
    if (!user) return;
    deleteCommentMutation.mutate(commentId);
  };

  const getInitials = (name: string) => {
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen relative bg-transparent">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-purple-500/10 pointer-events-none" />
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto relative z-10">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight">Community</h1>
            <p className="text-gray-400 mt-2">Connect and share with other quantum explorers</p>
          </div>
          {user && (
            <Button
              onClick={() => setShowCreatePost(!showCreatePost)}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg shadow-blue-500/20"
            >
              <PlusCircle className="mr-2 h-4 w-4" />
              {showCreatePost ? 'Cancel' : 'New Post'}
            </Button>
          )}
        </div>

        {user && showCreatePost && (
          <Card className="bg-slate-900/60 border-slate-700/50 backdrop-blur-md mb-8 overflow-hidden animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="h-1 bg-gradient-to-r from-blue-500 to-purple-600" />
            <CardContent className="p-6">
              <form onSubmit={submit} className="space-y-4">
                <Input
                  placeholder="Catchy Title"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  className="bg-slate-800/50 border-slate-700 text-white placeholder:text-gray-500 focus:ring-blue-500/50"
                />
                <Textarea
                  placeholder="Share your quantum insights..."
                  value={body}
                  onChange={e => setBody(e.target.value)}
                  className="bg-slate-800/50 border-slate-700 text-white placeholder:text-gray-500 focus:ring-blue-500/50 min-h-[120px]"
                />
                <div className="flex justify-end">
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                    <Send className="mr-2 h-4 w-4" />
                    Publish Post
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        )}

        {!loading && posts.length === 0 && (
          <Card className="bg-slate-900/40 border-slate-800 border-dashed backdrop-blur-sm py-12">
            <CardContent className="flex flex-col items-center text-center">
              <MessageSquare className="h-12 w-12 text-slate-700 mb-4" />
              <p className="text-gray-400 text-lg">No posts yet. Be the first to start a conversation!</p>
            </CardContent>
          </Card>
        )}

        <div className="space-y-6">
          {posts.map(p => {
            const likeCount = p.likes?.length ?? 0;
            const commentCount = p.comments?.length ?? 0;
            const likedByMe = (p.likes ?? []).some((l: any) => l.user_id === user?.id?.toString());
            const authorName = p.author?.name || p.author?.email || 'Anonymous';

            return (
              <Card key={p.id} className="bg-slate-900/60 border-slate-800 backdrop-blur-md hover:border-slate-700/50 transition-all duration-300 group">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-10 w-10 border border-blue-500/20">
                        <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${authorName}`} />
                        <AvatarFallback className="bg-blue-500/10 text-blue-400 text-xs">
                          {getInitials(authorName)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="text-white font-semibold flex items-center gap-2">
                          {authorName}
                          {p.author?.role === 'root' && <span className="bg-blue-500/20 text-blue-400 text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">Root</span>}
                        </div>
                        <div className="text-xs text-slate-500">
                          {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recently'}
                        </div>
                      </div>
                    </div>
                    {canModerate(p.author?.id) && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deletePost(p.id)}
                        className="text-slate-500 hover:text-red-400 hover:bg-red-400/10 h-8 w-8"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  <h3 className="text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">{p.title}</h3>
                  <p className="text-slate-300 whitespace-pre-wrap mb-6 leading-relaxed">{p.body}</p>

                  <div className="flex items-center gap-6 pt-4 border-t border-slate-800">
                    <button
                      onClick={() => toggleLike(p.id)}
                      className={`flex items-center gap-2 text-sm transition-colors ${likedByMe ? 'text-red-400' : 'text-slate-400 hover:text-red-400'}`}
                    >
                      <Heart className={`h-5 w-5 ${likedByMe ? 'fill-current' : ''}`} />
                      <span className="font-medium">{likeCount}</span>
                    </button>
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <MessageSquare className="h-5 w-5" />
                      <span className="font-medium">{commentCount}</span>
                    </div>
                  </div>

                  <div className="mt-6 space-y-4">
                    {p.comments && p.comments.length > 0 && (
                      <div className="space-y-3 bg-slate-950/40 rounded-xl p-4 border border-slate-800/50">
                        {p.comments.map((c: any) => (
                          <div key={c.id} className="flex gap-3 animate-in fade-in duration-300">
                            <Avatar className="h-7 w-7 mt-0.5">
                              <AvatarImage src={`https://api.dicebear.com/7.x/bottts/svg?seed=${c.author?.name || 'anon'}`} />
                              <AvatarFallback className="text-[10px]">{getInitials(c.author?.name || '??')}</AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-blue-400">{c.author?.name || 'Anonymous'}</span>
                                {canModerate(c.author?.id) && (
                                  <button onClick={() => deleteComment(c.id)} className="text-[10px] text-slate-600 hover:text-red-400 uppercase font-bold">Delete</button>
                                )}
                              </div>
                              <p className="text-sm text-slate-300 mt-0.5">{c.body}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {user && (
                      <div className="relative">
                        <Input
                          placeholder="Write a supportive comment..."
                          className="bg-slate-800/30 border-slate-700/50 text-white text-sm pr-12 focus:ring-blue-500/30 h-10 rounded-lg"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              const target = e.target as HTMLInputElement;
                              if (target.value.trim()) {
                                addComment(p.id, target.value);
                                target.value = '';
                              }
                            }
                          }}
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] uppercase font-bold text-slate-600 pointer-events-none">
                          Enter
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Community;



