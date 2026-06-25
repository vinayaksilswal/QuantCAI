import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title: string;
  description: string;
  keywords?: string;
  type?: string;
  url?: string;
  image?: string;
}

export const SEO = ({ 
  title, 
  description, 
  keywords = "quantum computing, quantum simulation, PQC scanner, quantum algorithms", 
  type = "website",
  url = "https://quantcai.in",
  image = "/og-image.png"
}: SEOProps) => {
  return (
    <Helmet>
      {/* Standard metadata tags */}
      <title>{title}</title>
      <meta name="description" content={description} />
      {keywords && <meta name="keywords" content={keywords} />}

      {/* Open Graph tags for social sharing */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={image} />

      {/* Twitter Card tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
    </Helmet>
  );
};
