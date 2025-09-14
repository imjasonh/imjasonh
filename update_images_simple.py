#!/usr/bin/env python3
import os
import glob

# Mapping of exact URLs to local paths
url_to_local = {
    # Multi-layer containers
    "https://images.ctfassets.net/l47ir7rfykkn/4JLY5nZcjGRnOXH6bfo3lQ/f753ea3498aabd5cd317018cd85db493/Single_vs_Multi_Layer_Image.png": "../blog-images/multi_layer_containers_img1.png",
    
    # Chainguard factory
    "https://images.ctfassets.net/l47ir7rfykkn/66P2iHr1QRLhCvtWK2SER9/ed727148e5be1e56b2846a36b08782c8/Inside_the_Chainguard_Factory_1.jpg": "../blog-images/chainguard_factory_img1.jpg",
    "https://images.ctfassets.net/l47ir7rfykkn/1IYiQAfZmNHIcJ87yxub95/7e8e48c5304fceef4014716994be1948/Inside_the_Chainguard_Factory_2.jpg": "../blog-images/chainguard_factory_img2.jpg",
    "https://images.ctfassets.net/l47ir7rfykkn/62ObbdO5vNmdnRLwhtwOq6/2150f8dd22fd98a9c085be6f408a5547/robots-welding-in-factory-156642859_1275x824_1_.jpeg": "../blog-images/chainguard_factory_img3.jpeg",
    "https://images.ctfassets.net/l47ir7rfykkn/4NfEmCbC5Ea8J9sZNmlIT5/99cf1e035c3083e69a28babfc674a37f/Inside_the_Chainguard_Factory_4.png": "../blog-images/chainguard_factory_img4.png",
    "https://images.ctfassets.net/l47ir7rfykkn/7GIKuPFznCe7YHXm0qrBOr/95207620017c40d52181be5053ae602b/Inside_the_Chainguard_Factory_5.jpg": "../blog-images/chainguard_factory_img5.jpg",
    "https://images.ctfassets.net/l47ir7rfykkn/SGX1JmB9cqcvc2KJRzeg9/cd4f27297ee3e6b48db05af1cbcb321b/Inside_the_Chainguard_Factory_6.jpg": "../blog-images/chainguard_factory_img6.jpg",
    
    # Vulnerability scanner
    "https://images.ctfassets.net/l47ir7rfykkn/7a3GoN7cCyomdbtW7lnS7K/2dbb1e53b97ce10202f732fa6bd53d98/this_shit_is_hard_scanners_image.jpg": "../blog-images/vulnerability_scanner_integration_img1.jpg",
    
    # Tagging philosophy
    "https://images.ctfassets.net/l47ir7rfykkn/3CDkDsPqCc7ESb85FqK5jg/9d7d83863bd20584d1709051b067e506/Chainguard-s_image_tagging_philosophy-_enabling_high_velocity_updates__pt._1_of_3__img1.jpeg": "../blog-images/tagging_philosophy_part1_img1.jpeg",
    "https://images.ctfassets.net/l47ir7rfykkn/1tpkxacnSuGzdbC7qX2Pe3/5468e044b4405dafc16c82bc2ea33c17/img.jpeg": "../blog-images/tagging_philosophy_part2_img1.jpeg",
    "https://images.ctfassets.net/l47ir7rfykkn/1qWX5ozqsb98OeZ0HDHGSw/2ba17d34352547a9e429ad9cdc48f838/Image_tagging_philosophy_pt_3.1.jpeg": "../blog-images/tagging_philosophy_part3_img1.jpeg",
    
    # Wolfi workstations
    "https://images.ctfassets.net/l47ir7rfykkn/3teHrDRKvjyF84IkHju8sI/9c41b35968bcd7e45b5ef4e0e85060b4/Wolfi_at_work_1.jpeg": "../blog-images/wolfi_workstations_img1.jpeg",
    "https://images.ctfassets.net/l47ir7rfykkn/6Fe34KGDSn8e4W7CjjHtj6/6d98bac75fea60f3cceed469f6db0dc0/Wolfi_at_work_2.png": "../blog-images/wolfi_workstations_img2.png",
    "https://images.ctfassets.net/l47ir7rfykkn/3ephxxjOIIeckHPv2Yeyn5/787507adc4b1bfaa33e51a5852e2110a/Wolfi_at_work_3.gif": "../blog-images/wolfi_workstations_img3.gif",
    
    # Most vulnerable image
    "https://images.ctfassets.net/l47ir7rfykkn/6gAajNsfsKCxhznkQAkq48/d28f95b0b9ece289f333563c1869cdb7/The_story_of_the_most_vulnerable_Chainguard_Image__1.png": "../blog-images/most_vulnerable_image_img1.png",
    "https://images.ctfassets.net/l47ir7rfykkn/abShG9CFVSUcvhH2cp9AM/2e20ae2179501a49e99893a0667ea95d/The_story_of_the_most_vulnerable_Chainguard_Image__2.png": "../blog-images/most_vulnerable_image_img2.png",
    
    # GHCR private repos
    "https://images.ctfassets.net/l47ir7rfykkn/5RXyV4rPfzp5cUj9ZwGg7F/1e014c8d3f9d856cccf6320f1966ec2a/ghcr_1.png": "../blog-images/ghcr_private_repos_img1.png",
    
    # Container registry
    "https://images.ctfassets.net/l47ir7rfykkn/3FfY9TNHibxsgpcEFthGPc/5f0aac3c8928a7d128fc1fbfc02943e0/image_registry_1.png": "../blog-images/container_registry_img1.png",
    
    # Immutable tags
    "https://images.ctfassets.net/l47ir7rfykkn/4tm72ifHZIKcharcRY5lVW/5e882fcfecc22451f20c232dbcb5f7bb/immutable_tags_1.jpeg": "../blog-images/immutable_tags_rekor_img1.jpeg",
}

def main():
    md_files = glob.glob('blog-posts-markdown/*.md')
    
    for md_file in md_files:
        print(f"Processing {os.path.basename(md_file)}...")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements_made = 0
        
        # Replace each URL
        for old_url, new_path in url_to_local.items():
            if old_url in content:
                content = content.replace(old_url, new_path)
                replacements_made += 1
                print(f"  ✓ Replaced image URL")
        
        # Write back if changes were made
        if replacements_made > 0:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Updated {replacements_made} image(s)")
        else:
            print(f"  No images to update")

if __name__ == "__main__":
    main()