package com.example.photoviewer;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import java.util.List;

public class ImageAdapter extends RecyclerView.Adapter<ImageAdapter.ImageViewHolder> {
    interface OnPostClick { void onClick(PostItem post); }
    private List<PostItem> posts;
    private final OnPostClick listener;
    public ImageAdapter(List<PostItem> posts, OnPostClick listener) { this.posts = posts; this.listener = listener; }
    /** Applies only the differences so the list keeps its scroll position. */
    void update(List<PostItem> newPosts) {
        List<PostItem> oldPosts = posts;
        DiffUtil.DiffResult diff = DiffUtil.calculateDiff(new DiffUtil.Callback() {
            @Override public int getOldListSize() { return oldPosts.size(); }
            @Override public int getNewListSize() { return newPosts.size(); }
            @Override public boolean areItemsTheSame(int oldPosition, int newPosition) {
                return oldPosts.get(oldPosition).id == newPosts.get(newPosition).id;
            }
            @Override public boolean areContentsTheSame(int oldPosition, int newPosition) {
                PostItem before = oldPosts.get(oldPosition);
                PostItem after = newPosts.get(newPosition);
                return before.title.equals(after.title) && before.text.equals(after.text)
                        && before.tags.equals(after.tags) && before.comments.equals(after.comments);
            }
        });
        posts = newPosts;
        diff.dispatchUpdatesTo(this);
    }
    @NonNull @Override public ImageViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        return new ImageViewHolder(LayoutInflater.from(parent.getContext()).inflate(R.layout.item_image, parent, false));
    }
    @Override public void onBindViewHolder(@NonNull ImageViewHolder holder, int position) {
        PostItem post = posts.get(position);
        holder.itemView.setOnClickListener(v -> listener.onClick(post));
        holder.imageView.setImageBitmap(post.image);
        holder.title.setText(post.title);
        holder.body.setText(post.text);
        List<String> statuses = new ArrayList<>();
        List<String> plainTags = new ArrayList<>();
        for (String tag : post.tags) {
            if (tag.equals("auth:unknown")) statuses.add("미등록자");
            else if (tag.equals("auth:no-face")) statuses.add("얼굴 없음");
            else if (tag.startsWith("auth:")) statuses.add("인증: " + tag.substring(5));
            else plainTags.add(tag);
        }
        holder.auth.setVisibility(statuses.isEmpty() ? View.GONE : View.VISIBLE);
        holder.auth.setText(String.join(", ", statuses));
        String tagText = plainTags.isEmpty() ? "" : "#" + String.join(" #", plainTags);
        String commentText = post.comments.isEmpty() ? "" : "\n댓글: " + String.join(" · ", post.comments);
        holder.tags.setText(tagText + commentText);
    }
    @Override public int getItemCount() { return posts.size(); }
    static class ImageViewHolder extends RecyclerView.ViewHolder {
        final ImageView imageView; final TextView title; final TextView body; final TextView tags; final TextView auth;
        ImageViewHolder(View itemView) { super(itemView); imageView=itemView.findViewById(R.id.imageViewItem); title=itemView.findViewById(R.id.postTitle); body=itemView.findViewById(R.id.postBody); tags=itemView.findViewById(R.id.postTags); auth=itemView.findViewById(R.id.postAuth); }
    }
}
