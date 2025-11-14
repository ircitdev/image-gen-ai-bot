// Cloudflare Worker для генерации изображений через Hugging Face
// Деплой на workers.cloudflare.com

export default {
  async fetch(request, env, ctx) {
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const { prompt } = await request.json();

      if (!prompt) {
        return new Response(JSON.stringify({ error: 'Prompt is required' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Используем новый API Hugging Face Inference Router
      const API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell";

      // Вставьте сюда свой Hugging Face API токен
      const HF_TOKEN = env.HUGGINGFACE_TOKEN || "YOUR_HF_TOKEN_HERE";

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${HF_TOKEN}`,
          'Content-Type': 'application/json',
          'x-use-cache': 'false'
        },
        body: JSON.stringify({
          inputs: prompt
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        console.error('HF API Error:', error);
        return new Response(JSON.stringify({
          error: 'Image generation failed',
          details: error
        }), {
          status: response.status,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Получаем изображение как blob
      const imageBlob = await response.blob();

      // Конвертируем в base64
      const arrayBuffer = await imageBlob.arrayBuffer();
      const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

      return new Response(JSON.stringify({
        success: true,
        image: `data:image/png;base64,${base64}`
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });

    } catch (error) {
      console.error('Worker Error:', error);
      return new Response(JSON.stringify({
        error: 'Internal server error',
        message: error.message
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};
