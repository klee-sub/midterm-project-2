package com.example.photoviewer;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class ImageAdapter extends RecyclerView.Adapter<ImageAdapter.ImageViewHolder> {
    interface OnPostClick { void onClick(PostItem post); }
    private final List<PostItem> posts;
    private final OnPostClick listener;
    public ImageAdapter(List<PostItem> posts, OnPostClick listener) { this.posts = posts; this.listener = listener; }
    @NonNull @Override public ImageViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        return new ImageViewHolder(LayoutInflater.from(parent.getContext()).inflate(R.layout.item_image, parent, false));
    }
    @Override public void onBindViewHolder(@NonNull ImageViewHolder holder, int position) {
        PostItem post = posts.get(position);
        holder.itemView.setOnClickListener(v -> listener.onClick(post));
        holder.imageView.setImageBitmap(post.image);
        holder.title.setText(post.title);
        holder.body.setText(post.text);
        String tagText = post.tags.isEmpty() ? "" : "#" + String.join(" #", post.tags);
        String commentText = post.comments.isEmpty() ? "" : "\n댓글: " + String.join(" · ", post.comments);
        holder.tags.setText(tagText + commentText);
    }
    @Override public int getItemCount() { return posts.size(); }
    static class ImageViewHolder extends RecyclerView.ViewHolder {
        final ImageView imageView; final TextView title; final TextView body; final TextView tags;
        ImageViewHolder(View itemView) { super(itemView); imageView=itemView.findViewById(R.id.imageViewItem); title=itemView.findViewById(R.id.postTitle); body=itemView.findViewById(R.id.postBody); tags=itemView.findViewById(R.id.postTags); }
    }
}
