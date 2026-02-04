<?php
/**
 * Plugin Name:        Agep Okul Eklentisi
 * Description:        Görme engelli öğrenciler için deneme sınavı ve ödev sistemi sağlayan özel okul eklentisi. (AJAX Modeli + Sesli Soru Desteği)
 * Version:            9.2 (Audio Support)
 * Author:             Kodlama Desteği (Gemini) & Agep
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// === TEMEL KURULUM VE ROLLER ===
register_activation_hook( __FILE__, 'agep_plugin_activation' );
function agep_plugin_activation() {
	global $wpdb;
	$table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
	$charset_collate = $wpdb->get_charset_collate();
	$sql = "CREATE TABLE $table_name (
		sonuc_id bigint(20) NOT NULL AUTO_INCREMENT,
		ogrenci_id bigint(20) NOT NULL,
		sinav_id bigint(20) NOT NULL,
		tarih datetime NOT NULL,
		dogru_sayisi int(11) NOT NULL,
		yanlis_sayisi int(11) NOT NULL,
		bos_sayisi int(11) NOT NULL,
		net_puan float NOT NULL,
		cevaplar longtext NOT NULL,
		PRIMARY KEY (sonuc_id),
		KEY sinav_id (sinav_id),
		KEY ogrenci_sinav (ogrenci_id, sinav_id)
	) $charset_collate;";
	require_once( ABSPATH . 'wp-admin/includes/upgrade.php' );
	dbDelta( $sql );

	$caps = [
		'edit_sinav' => true,
		'read_sinav' => true,
		'delete_sinav' => true,
		'edit_sinavs' => true,
		'edit_others_sinavs' => true,
		'publish_sinavs' => true,
		'read_private_sinavs' => true,
		'delete_sinavs' => true,
		'delete_published_sinavs' => true,
		'delete_others_sinavs' => true,
		'edit_published_sinavs' => true,
		'read' => true,
	];
	add_role('egitmen', 'Eğitmen', $caps);
	$admin_role = get_role('administrator');
	if ($admin_role) {
		foreach ($caps as $cap => $grant) { if ($grant) $admin_role->add_cap($cap); }
	}
}

// === POST TİPLERİ VE MENÜLER ===
add_action( 'init', 'agep_register_post_types' );
function agep_register_post_types() {
	register_post_type( 'sinav', [
		'labels' => [
			'name' => 'Sınavlar',
			'singular_name' => 'Sınav',
			'menu_name' => 'Sınavlar',
			'add_new_item' => 'Yeni Sınav Ekle'
		],
		'supports' => ['title', 'editor', 'author'],
		'public' => true,
		'show_ui' => true,
		'show_in_menu' => true,
		'menu_position' => 5,
		'menu_icon' => 'dashicons-welcome-learn-more',
		'has_archive' => false,
		'publicly_queryable' => false,
		'capability_type' => 'sinav',
		'map_meta_cap' => true
	]);
}
add_action( 'admin_menu', 'agep_add_admin_pages' );
function agep_add_admin_pages() {
	add_submenu_page( 'edit.php?post_type=sinav', 'Sınav Sonuçları', 'Sınav Sonuçları', 'edit_posts', 'agep-sinav-sonuclari', 'agep_admin_results_page_html' );
}

// === FİLTRELER VE ERİŞİM KONTROLLERİ ===
add_action( 'pre_get_posts', 'agep_filter_exams_by_author' );
function agep_filter_exams_by_author( $query ) {
	if ( ! is_admin() || ! $query->is_main_query() ) return;
	$user = wp_get_current_user();
	if ( in_array('egitmen', (array) $user->roles) && !current_user_can('manage_options') ) {
		if ( $query->get('post_type') == 'sinav' ) {
			$query->set('author', $user->ID);
		}
	}
}

add_action('admin_init', 'agep_block_instructor_admin_access');
function agep_block_instructor_admin_access() {
	$user = wp_get_current_user();
	if ( in_array('egitmen', (array) $user->roles) && !current_user_can('manage_options') ) {
		if ( ! wp_doing_ajax() ) {
			wp_redirect( home_url('/egitmen-paneli/') );
			exit;
		}
	}
}

add_action('after_setup_theme', 'agep_remove_admin_bar');
function agep_remove_admin_bar() {
	$user = wp_get_current_user();
	if ( in_array('egitmen', (array) $user->roles) && !current_user_can('manage_options') ) {
		show_admin_bar(false);
	}
}

add_action('admin_init', 'agep_redirect_backend_exam_editor');
function agep_redirect_backend_exam_editor() {
	global $pagenow;
	if ($pagenow == 'post-new.php' && isset($_GET['post_type']) && $_GET['post_type'] == 'sinav') {
		wp_redirect(home_url('/sinav-yonetimi/'));
		exit;
	}
	if ($pagenow == 'post.php' && isset($_GET['post'])) {
		$post_id = absint($_GET['post']);
		if (get_post_type($post_id) == 'sinav') {
			$redirect_url = add_query_arg('sinav_id', $post_id, home_url('/sinav-yonetimi/'));
			wp_redirect($redirect_url);
			exit;
		}
	}
}

// === STİL VE SCRIPT DOSYALARI ===
add_action( 'wp_enqueue_scripts', 'agep_frontend_assets' );
function agep_frontend_assets() {
	// CSS
	wp_enqueue_style('agep-style', plugin_dir_url( __FILE__ ) . 'assets/css/agep-style.css', [], '2.2');
	
	// JS ve Medya Yükleyici
	wp_enqueue_script('jquery');
	
	// WordPress Medya Kütüphanesini Çağır (Ses dosyası yüklemek için gerekli)
	if( current_user_can('edit_sinavs') ) {
		wp_enqueue_media();
	}
	
	global $post;
	if ( is_a( $post, 'WP_Post' ) && has_shortcode( $post->post_content, 'agep_sinav_formu' ) ) {
		wp_enqueue_editor();
	}
	
	wp_register_script('agep-main-script', false);
	wp_enqueue_script('agep-main-script');
	
	wp_localize_script('agep-main-script', 'agep_ajax_obj', [
		'ajax_url' => admin_url('admin-ajax.php'),
		'nonce' => wp_create_nonce('agep_ajax_nonce'),
		'delete_nonce' => wp_create_nonce('agep_delete_exam_nonce'),
		'autosave_nonce' => wp_create_nonce('agep_autosave_nonce') 
	]);
}

// === CSV DIŞA AKTARMA (Sonuçlar + Soru Analizi) ===
add_action('init', 'agep_handle_csv_export');
function agep_handle_csv_export() {
	if (isset($_GET['action']) && $_GET['action'] === 'agep_export_csv' && isset($_GET['sinav_id']) && isset($_GET['nonce'])) {
		$sinav_id = absint($_GET['sinav_id']);
		$type = isset($_GET['type']) ? sanitize_key($_GET['type']) : 'results';

		if (!wp_verify_nonce($_GET['nonce'], 'agep_export_nonce_' . $sinav_id)) {
			wp_die('Güvenlik kontrolü başarısız.');
		}
		if (!current_user_can('edit_post', $sinav_id)) {
			wp_die('Bu veriyi dışa aktarma yetkiniz yok.');
		}

		global $wpdb;
		$table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
		$sinav = get_post($sinav_id);

		nocache_headers();
		header('Content-Type: text/csv; charset=utf-8');

		if ($type === 'analysis') {
			$filename = 'soru-analizi-' . sanitize_title($sinav->post_title) . '-' . date('Y-m-d') . '.csv';
			header('Content-Disposition: attachment; filename="' . $filename . '"');
			$output = fopen('php://output', 'w'); fputs($output, "\xEF\xBB\xBF");
			$sorular = get_post_meta($sinav_id, '_sinav_sorulari_data', true);
			$rows = $wpdb->get_results($wpdb->prepare("SELECT cevaplar FROM $table_name WHERE sinav_id = %d", $sinav_id));
			$items = agep_build_item_analysis($sorular, $rows);
			fputcsv($output, ['Soru No', 'Doğru %', 'Doğru', 'Yanlış', 'Boş', 'Doğru Cevap', 'Soru Metni']);
			$toplam = count($rows) ?: 1;
			foreach ($items as $i => $row) {
				$s = isset($sorular[$i]) ? $sorular[$i] : [];
				$pct = ($row['dogru'] / $toplam) * 100;
				fputcsv($output, [
					$i + 1,
					number_format($pct, 2, ',', '.'),
					$row['dogru'],
					$row['yanlis'],
					$row['bos'],
					isset($s['dogru_cevap']) ? strtoupper($s['dogru_cevap']) : '',
					isset($s['metin']) ? wp_strip_all_tags($s['metin']) : ''
				]);
			}
			fclose($output);
			exit;
		} else {
			$sonuclar = $wpdb->get_results($wpdb->prepare("SELECT * FROM $table_name WHERE sinav_id = %d ORDER BY tarih DESC", $sinav_id));
			$filename = 'sinav-sonuclari-' . sanitize_title($sinav->post_title) . '-' . date('Y-m-d') . '.csv';
			header('Content-Disposition: attachment; filename="' . $filename . '"');
			$output = fopen('php://output', 'w'); fputs($output, "\xEF\xBB\xBF");
			fputcsv($output, ['Öğrenci Adı', 'Öğrenci Email', 'Tarih', 'Doğru', 'Yanlış', 'Boş', 'Net Puan']);
			if (!empty($sonuclar)) {
				foreach ($sonuclar as $sonuc) {
					$ogrenci = get_userdata($sonuc->ogrenci_id);
					$row = [
						$ogrenci ? $ogrenci->display_name : 'Bilinmiyor',
						$ogrenci ? $ogrenci->user_email : 'Bilinmiyor',
						date_i18n('d-m-Y H:i', strtotime($sonuc->tarih)),
						$sonuc->dogru_sayisi,
						$sonuc->yanlis_sayisi,
						$sonuc->bos_sayisi,
						number_format($sonuc->net_puan, 2, ',', '.')
					];
					fputcsv($output, $row);
				}
			}
			fclose($output);
			exit;
		}
	}
}

// === YARDIMCI FONKSİYONLAR ===
function agep_sinav_ayarlari_meta_box_html( $post ) {
	$post_id = is_object($post) ? $post->ID : 0;
	$sure = get_post_meta( $post_id, '_sinav_sure', true );
	$puanlama = get_post_meta( $post_id, '_sinav_puanlama', true );
	$hedef_roller = get_post_meta( $post_id, '_sinav_hedef_rol', true );
    if ( !is_array($hedef_roller) ) {
        $hedef_roller = [];
    }
	?>
	<p><label for="agep_sinav_sure"><b>Sınav Süresi (dakika olarak, boş bırakırsanız süresiz olur):</b></label><br><input type="number" id="agep_sinav_sure" name="agep_sinav_sure" value="<?php echo esc_attr( $sure ); ?>" style="width:100%;" /></p>
	<p><label for="agep_sinav_puanlama"><b>Puanlama Yöntemi:</b></label><br>
		<select name="agep_sinav_puanlama" id="agep_sinav_puanlama" style="width:100%;">
			<option value="standart" <?php selected( $puanlama, 'standart' ); ?>>Standart (Sadece doğrular)</option>
			<option value="net" <?php selected( $puanlama, 'net' ); ?>>Net Hesaplama (4 Yanlış 1 Doğruyu Götürür)</option>
		</select>
	</p>
	<p><label><b>Hedef Kitle (Rol):</b><br><small>Hiçbir rol seçilmezse sınav tüm öğrencilere açık olur.</small></label><br>
        <div class="agep-role-checkbox-group" style="height: 150px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; background-color: #fff;">
            <?php
            global $wp_roles;
            $all_roles = $wp_roles->roles;
            $istenmeyen_roller = ['administrator', 'bbp_keymaster', 'bbp_participant', 'translator', 'wpas_agent', 'wpas_support_manager', 'wpas_user', 'agena_renci', 'editor', 'agena_ynetim', 'author', 'egitmen'];
            
            foreach ($all_roles as $rol_slug => $rol_detay) {
                if (in_array($rol_slug, $istenmeyen_roller)) {
                    continue;
                }
                ?>
                <label for="role-<?php echo esc_attr($rol_slug); ?>" style="display: block; margin-bottom: 5px;">
                    <input 
                        type="checkbox" 
                        name="agep_sinav_hedef_rol[]" 
                        id="role-<?php echo esc_attr($rol_slug); ?>" 
                        value="<?php echo esc_attr($rol_slug); ?>"
                        <?php checked(in_array($rol_slug, $hedef_roller)); ?>
                    >
                    <?php echo esc_html($rol_detay['name']); ?>
                </label>
                <?php
            } 
            ?>
        </div>
	</p>
	<?php
}
function agep_sinav_sorulari_meta_box_html( $post ) {
    $post_id = is_object($post) ? $post->ID : 0;
    $sorular = get_post_meta($post_id, '_sinav_sorulari_data', true);
    if (!is_array($sorular)) $sorular = [];
    
    echo '<div id="agep-soru-container">';
    if (empty($sorular)) echo '<p>Henüz soru eklenmedi.</p>';
    
    foreach ($sorular as $i => $s) {
        $id_bolum = "soru-{$i}-bolum";
        $id_puan = "soru-{$i}-puan";
        // Ses dosyası verisi
        $ses_dosyasi = isset($s['ses_dosyasi']) ? $s['ses_dosyasi'] : '';
        
        echo '<div class="agep-soru-tekil" style="border:1px solid #ccc; padding:15px; margin-bottom:15px; background:#f9f9f9;">
            <button type="button" class="button agep-soru-kaldir" style="float:right;">Soruyu Kaldır</button>
            
            <div style="background:#e3f2fd; padding:10px; border-left:4px solid #2196f3; margin-bottom:10px;">
                <div style="display:flex; gap:10px;">
                    <div style="flex-grow:1;">
                        <label for="'.$id_bolum.'"><b>Bölüm Başlığı (Yeni Sayfa):</b></label>
                        <input type="text" id="'.$id_bolum.'" name="sorular['.$i.'][bolum_basligi]" value="'.esc_attr($s['bolum_basligi']??'').'" style="width:100%; font-weight:bold; color:#0d47a1;" placeholder="Örn: Matematik Testi">
                    </div>
                    <div style="width:150px;">
                        <label for="'.$id_puan.'"><b>Soru Puanı:</b></label>
                        <input type="number" step="0.01" id="'.$id_puan.'" name="sorular['.$i.'][bolum_puani]" value="'.esc_attr($s['bolum_puani']??'').'" style="width:100%;" placeholder="Örn: 3.5">
                        <small style="font-size:10px; color:#666;">Bu bölümdeki her soru kaç puan?</small>
                    </div>
                </div>
            </div>

            <p style="background:#fff3e0; padding:10px; border:1px solid #ffe0b2;">
                <label><b>🔊 Sesli Soru (Opsiyonel):</b></label><br>
                <input type="text" class="agep-ses-input" name="sorular['.$i.'][ses_dosyasi]" value="'.esc_attr($ses_dosyasi).'" style="width:70%;" placeholder="Ses dosyası URLsi buraya gelecek...">
                <button type="button" class="button agep-medya-yukle">Ses Dosyası Yükle</button>
            </p>

            <p><label><b>Soru '.($i+1).' Metni:</b></label><textarea name="sorular['.$i.'][metin]" style="width:100%;">'.esc_textarea($s['metin']).'</textarea></p>';
            
            foreach(['a','b','c','d','e'] as $opt) {
                echo '<p><label>'.strtoupper($opt).') </label> <input type="text" name="sorular['.$i.'][secenek_'.$opt.']" value="'.esc_attr($s['secenek_'.$opt]??'').'" style="width:90%;"></p>';
            }

            echo '<p><label>Doğru Cevap:</label> 
            <select name="sorular['.$i.'][dogru_cevap]"><option value="">Seç</option>';
            foreach(['a','b','c','d','e'] as $o) echo '<option value="'.$o.'" '.selected($s['dogru_cevap'],$o,false).'>'.strtoupper($o).'</option>';
            echo '</select></p>
            <p><label>Açıklama:</label><textarea name="sorular['.$i.'][aciklama]" style="width:100%;">'.esc_textarea($s['aciklama']).'</textarea></p>
        </div>';
    }
    echo '</div><button type="button" id="agep-yeni-soru-ekle" class="button button-primary">Yeni Soru Ekle</button>';
}
function agep_get_repeater_js_template() {
    ob_start(); ?>
    <script>jQuery(document).ready(function($){
        // MEDYA YÜKLEYİCİ MANTIĞI
        $(document).on('click', '.agep-medya-yukle', function(e) {
            e.preventDefault();
            var button = $(this);
            var custom_uploader = wp.media({
                title: 'Ses Dosyası Seç',
                button: { text: 'Bu Dosyayı Kullan' },
                multiple: false
            }).on('select', function() {
                var attachment = custom_uploader.state().get('selection').first().toJSON();
                button.prev('.agep-ses-input').val(attachment.url);
            }).open();
        });

        var c=$('#agep-soru-container');
        $('#agep-yeni-soru-ekle').click(function(){
            var i=c.find('.agep-soru-tekil').length;
            // Dinamik ID oluşturma
            var h=`<div class="agep-soru-tekil" style="border:1px solid #ccc; padding:15px; margin-bottom:15px; background:#f9f9f9;">
            <button type="button" class="button agep-soru-kaldir" style="float:right;">Soruyu Kaldır</button>
            <div style="background:#e3f2fd; padding:10px; border-left:4px solid #2196f3; margin-bottom:10px;">
                <label for="soru-${i}-bolum"><b>Bölüm Başlığı:</b></label><br>
                <input type="text" id="soru-${i}-bolum" name="sorular[${i}][bolum_basligi]" style="width:100%; font-weight:bold; color:#0d47a1;">
            </div>
            
            <p style="background:#fff3e0; padding:10px; border:1px solid #ffe0b2;">
                <label><b>🔊 Sesli Soru (Opsiyonel):</b></label><br>
                <input type="text" class="agep-ses-input" name="sorular[${i}][ses_dosyasi]" style="width:70%;" placeholder="Ses dosyası URLsi buraya gelecek...">
                <button type="button" class="button agep-medya-yukle">Ses Dosyası Yükle</button>
            </p>

            <p><label for="soru-${i}-metin"><b>Soru ${i+1} Metni:</b></label><br><textarea id="soru-${i}-metin" name="sorular[${i}][metin]" style="width:100%;"></textarea></p>
            <p><label for="soru-${i}-opt-a">A) </label><input type="text" id="soru-${i}-opt-a" name="sorular[${i}][secenek_a]" style="width:90%;"></p>
            <p><label for="soru-${i}-opt-b">B) </label><input type="text" id="soru-${i}-opt-b" name="sorular[${i}][secenek_b]" style="width:90%;"></p>
            <p><label for="soru-${i}-opt-c">C) </label><input type="text" id="soru-${i}-opt-c" name="sorular[${i}][secenek_c]" style="width:90%;"></p>
            <p><label for="soru-${i}-opt-d">D) </label><input type="text" id="soru-${i}-opt-d" name="sorular[${i}][secenek_d]" style="width:90%;"></p>
            <p><label for="soru-${i}-opt-e">E) </label><input type="text" id="soru-${i}-opt-e" name="sorular[${i}][secenek_e]" style="width:90%;"></p>
            <p><label for="soru-${i}-dogru">Doğru Cevap:</label> <select id="soru-${i}-dogru" name="sorular[${i}][dogru_cevap]"><option value="">Seç</option><option value="a">A</option><option value="b">B</option><option value="c">C</option><option value="d">D</option><option value="e">E</option></select></p>
            <p><label for="soru-${i}-aciklama">Açıklama:</label><br><textarea id="soru-${i}-aciklama" name="sorular[${i}][aciklama]" style="width:100%;"></textarea></p></div>`;
            c.append(h);
        });
        c.on('click','.agep-soru-kaldir',function(){$(this).closest('.agep-soru-tekil').remove();});
    });</script>
    <?php return ob_get_clean();
}
add_action('admin_footer-post.php', 'agep_print_repeater_js_if_sinav');
add_action('admin_footer-post-new.php', 'agep_print_repeater_js_if_sinav');
function agep_print_repeater_js_if_sinav() {
	$screen = function_exists('get_current_screen') ? get_current_screen() : null;
	if ($screen && $screen->post_type === 'sinav') {
		echo agep_get_repeater_js_template();
	}
}

// === İSTATİSTİK YARDIMCILARI ===
function agep_stats_basic($values){
	$n = count($values);
	if ($n === 0) return ['n'=>0,'mean'=>0,'min'=>0,'max'=>0,'std'=>0,'median'=>0];
	sort($values);
	$sum = array_sum($values);
	$mean = $sum / $n;
	$min = $values[0];
	$max = $values[$n-1];
	$var = 0.0; foreach ($values as $v){ $d=$v-$mean; $var += $d*$d; }
	$std = sqrt($var / $n);
	$median = ($n % 2) ? $values[intval($n/2)] : (($values[$n/2 - 1] + $values[$n/2]) / 2);
	return ['n'=>$n,'mean'=>$mean,'min'=>$min,'max'=>$max,'std'=>$std,'median'=>$median];
}
function agep_histogram($values, $bins = 8){
	if (empty($values)) return [[], []];
	$min = min($values); $max = max($values);
	if ($min == $max) { return [ [[$min, $max]], [count($values)] ]; }
	$width = ($max - $min) / $bins;
	if ($width <= 0) { return [ [[$min, $max]], [count($values)] ]; }
	$hist = array_fill(0, $bins, 0);
	foreach ($values as $v){
		$idx = (int) floor(($v - $min) / $width);
		if ($idx >= $bins) $idx = $bins - 1;
		$hist[$idx]++;
	}
	$ranges = [];
	for ($i=0; $i<$bins; $i++){
		$start = $min + $i * $width;
		$end = ($i === $bins-1) ? $max : ($start + $width);
		$ranges[] = [$start, $end];
	}
	return [$ranges, $hist];
}
function agep_build_item_analysis($sorular, $sonuclar){
	$adet = is_array($sorular) ? count($sorular) : 0;
	if ($adet === 0) return [];
	$items = [];
	for ($i=0; $i<$adet; $i++){ $items[$i] = ['dogru'=>0,'yanlis'=>0,'bos'=>0]; }
	foreach ($sonuclar as $s) {
		$cev_json = is_object($s) ? $s->cevaplar : (isset($s['cevaplar']) ? $s['cevaplar'] : '');
		$cev = json_decode($cev_json, true);
		if (!is_array($cev)) $cev = [];
		foreach ($sorular as $i => $soru) {
			$ans = isset($cev[$i]) ? strtolower($cev[$i]) : '';
			$correct = isset($soru['dogru_cevap']) ? strtolower($soru['dogru_cevap']) : '';
			if ($ans === '' || $ans === 'bos') { $items[$i]['bos']++; }
			elseif ($ans === $correct) { $items[$i]['dogru']++; }
			else { $items[$i]['yanlis']++; }
		}
	}
	return $items;
}

// === VERİ KAYDETME VE AJAX ===
add_action('save_post_sinav','agep_save_sinav_postdata', 10, 1);
function agep_save_sinav_postdata($post_id){
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;
    
    if(isset($_POST['agep_sinav_sure'])) update_post_meta($post_id, '_sinav_sure', absint($_POST['agep_sinav_sure']));
    if(isset($_POST['agep_sinav_puanlama'])) update_post_meta($post_id, '_sinav_puanlama', sanitize_text_field($_POST['agep_sinav_puanlama']));
    if(isset($_POST['agep_sinav_hedef_rol'])) update_post_meta($post_id, '_sinav_hedef_rol', array_map('sanitize_text_field', $_POST['agep_sinav_hedef_rol']));
    else delete_post_meta($post_id, '_sinav_hedef_rol');

    if(isset($_POST['sorular']) && is_array($_POST['sorular'])){
        $clean = [];
        foreach ($_POST['sorular'] as $s) {
            if(empty(trim($s['metin']))) continue;
            $clean[] = [
                'metin' => wp_kses_post($s['metin']),
                'bolum_basligi' => sanitize_text_field($s['bolum_basligi']??''), 
                'bolum_puani' => floatval($s['bolum_puani']??0),
                'ses_dosyasi' => esc_url_raw($s['ses_dosyasi']??''), // YENİ EKLENDİ
                'secenek_a' => sanitize_text_field($s['secenek_a']??''),
                'secenek_b' => sanitize_text_field($s['secenek_b']??''),
                'secenek_c' => sanitize_text_field($s['secenek_c']??''),
                'secenek_d' => sanitize_text_field($s['secenek_d']??''),
                'secenek_e' => sanitize_text_field($s['secenek_e']??''),
                'dogru_cevap' => sanitize_text_field($s['dogru_cevap']??''),
                'aciklama' => wp_kses_post($s['aciklama']??'')
            ];
        }
        update_post_meta($post_id, '_sinav_sorulari_data', $clean);
    }
}

// === YENİ ÖZELLİK: OTOMATİK KAYIT (AUTOSAVE) ===
add_action('wp_ajax_agep_autosave_exam', 'agep_autosave_exam_ajax');
function agep_autosave_exam_ajax() {
    check_ajax_referer('agep_autosave_nonce', 'nonce');
    if (!is_user_logged_in()) wp_send_json_error();
    
    $sinav_id = absint($_POST['sinav_id']);
    $cevaplar = isset($_POST['cevaplar']) ? $_POST['cevaplar'] : [];
    
    // Cevapları geçici olarak user meta'da sakla
    update_user_meta(get_current_user_id(), 'agep_temp_answers_' . $sinav_id, $cevaplar);
    wp_send_json_success();
}

// === GÜNCELLENMİŞ SINAV GÖNDERİM FONKSİYONU (HIGH TRAFFIC) ===
add_action('wp_ajax_agep_submit_exam','agep_process_exam_ajax');
function agep_process_exam_ajax(){
    // Güvenlik kontrolü
	// check_ajax_referer('agep_ajax_nonce','nonce'); 
	
	if(!is_user_logged_in()){
		wp_send_json_error(['message' => 'Oturum süreniz dolmuş. Lütfen giriş yapın.']);
	}

	$sinav_id = absint($_POST['sinav_id']);
	$ogrenci_id = get_current_user_id();
	
	// KİLİT MEKANİZMASI (LOCKING): Aynı anda çift tıklamayı ve DB yığılmasını önler
	$lock_key = 'agep_lock_' . $ogrenci_id . '_' . $sinav_id;
	if ( get_transient( $lock_key ) ) {
		wp_send_json_error(['message' => 'İşleminiz şu an yapılıyor, lütfen bekleyin...']);
	}
	set_transient( $lock_key, true, 45 ); // 45 saniye kilitle
	
	try {
		global $wpdb;
		$table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
		$cevaplar = isset($_POST['cevaplar']) ? $_POST['cevaplar'] : [];

		// Daha önce çözdü mü kontrolü
		$mevcut = $wpdb->get_var($wpdb->prepare(
			"SELECT sonuc_id FROM $table_name WHERE ogrenci_id = %d AND sinav_id = %d LIMIT 1",
			$ogrenci_id, $sinav_id
		));
		if ($mevcut) { 
			wp_send_json_error(['message' => 'Bu sınavı zaten tamamladınız.']); 
		}

        // Yetki Kontrolü
		$sinav = get_post($sinav_id);
		$hedef_roller = get_post_meta($sinav_id, '_sinav_hedef_rol', true);
		if( !empty($hedef_roller) && is_array($hedef_roller) ) {
            $user = wp_get_current_user();
			$kesisim = array_intersect( (array) $user->roles, $hedef_roller );
			if ( empty($kesisim) ) wp_send_json_error(['message' => 'Yetkiniz yok.']);
		}

        // Puan Hesaplama
		$sorular = get_post_meta($sinav_id, '_sinav_sorulari_data', true);
		$dogru = 0; $yanlis = 0; $bos = 0;
		
        if(is_array($sorular)){
            foreach($sorular as $i => $soru){
                if (empty($soru['metin'])) continue;
                $cvp = isset($cevaplar[$i]) ? strtolower(sanitize_text_field($cevaplar[$i])) : '';
                $dgr = isset($soru['dogru_cevap']) ? strtolower($soru['dogru_cevap']) : '';
                
                if($cvp === '' || $cvp === 'bos'){ $bos++; }
                elseif($cvp === $dgr){ $dogru++; }
                else { $yanlis++; }
            }
        }

		$puan_tipi = get_post_meta($sinav_id, '_sinav_puanlama', true);
		$net = ($puan_tipi == 'net') ? ($dogru - ($yanlis / 4)) : $dogru;

		$wpdb->insert($table_name, [
			'ogrenci_id' => $ogrenci_id,
			'sinav_id' => $sinav_id,
			'tarih' => current_time('mysql'),
			'dogru_sayisi' => $dogru, 'yanlis_sayisi' => $yanlis, 'bos_sayisi' => $bos,
			'net_puan' => $net,
			'cevaplar' => json_encode($cevaplar)
		]);

		// İşlem başarılı, geçici verileri temizle
		delete_user_meta($ogrenci_id, "agep_sinav_{$sinav_id}_start");
        delete_user_meta($ogrenci_id, 'agep_temp_answers_' . $sinav_id);

		$sonuc_id = $wpdb->insert_id;
		$redirect_url = add_query_arg('sonuc_id', $sonuc_id, home_url('/sonuclar'));
		wp_send_json_success(['redirect_url' => $redirect_url]);

	} catch (Exception $e) {
        wp_send_json_error(['message' => 'Sistem hatası.']);
    } finally {
		delete_transient( $lock_key );
	}
}
// =========== BİTİŞ: GÜNCELLENMİŞ FONKSİYON ===========


add_action('wp_ajax_agep_save_exam_from_frontend','agep_save_exam_from_frontend_ajax');
function agep_save_exam_from_frontend_ajax(){
	check_ajax_referer('agep_ajax_nonce','nonce');
	if(!current_user_can('edit_sinavs')){
		wp_send_json_error(['message' => 'Sınav kaydetme yetkiniz yok.']);
	}
	$sinav_id = isset($_POST['post_id']) ? absint($_POST['post_id']) : 0;
	$sinav_baslik = sanitize_text_field($_POST['post_title']);
	if(empty($sinav_baslik)){
		wp_send_json_error(['message' => 'Sınav başlığı boş olamaz.']);
	}
	$post_data = [
		'post_title' => $sinav_baslik,
		'post_content' => wp_kses_post($_POST['post_content']),
		'post_type' => 'sinav',
		'post_status' => 'publish',
		'post_author' => get_current_user_id()
	];
	if($sinav_id > 0){ $post_data['ID'] = $sinav_id; }
	$yeni_sinav_id = wp_insert_post($post_data, true);
	if(is_wp_error($yeni_sinav_id)){
		wp_send_json_error(['message' => $yeni_sinav_id->get_error_message()]);
	}
	
	agep_save_sinav_postdata($yeni_sinav_id);
	
	wp_send_json_success(['message' => 'Sınav başarıyla kaydedildi!', 'redirect_url' => home_url('/egitmen-sonuclari/')]);
}

add_action('wp_ajax_agep_delete_exam', 'agep_delete_exam_ajax');
function agep_delete_exam_ajax() {
	check_ajax_referer('agep_delete_exam_nonce', 'nonce');
	$post_id = isset($_POST['sinav_id']) ? absint($_POST['sinav_id']) : 0;
	if ($post_id === 0) { wp_send_json_error(['message' => 'Geçersiz Sınav ID.']); }
	if (!current_user_can('delete_post', $post_id)) { wp_send_json_error(['message' => 'Bu sınavı silme yetkiniz yok.']); }
	global $wpdb;
	$table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
	$wpdb->delete($table_name, ['sinav_id' => $post_id], ['%d']);
	$result = wp_delete_post($post_id, true);
	if ($result === false) { wp_send_json_error(['message' => 'Sınav silinirken bir hata oluştu.']); }
	wp_send_json_success(['message' => 'Sınav ve ilgili tüm sonuçlar başarıyla silindi.']);
}

// === KISA KODLAR (SHORTCODES) ===
add_shortcode('agep_ogrenci_paneli','agep_ogrenci_paneli_shortcode');
add_shortcode('agep_sinav_ekrani','agep_sinav_ekrani_shortcode');
add_shortcode('agep_sonuc_ekrani','agep_sonuc_ekrani_shortcode');
add_shortcode('agep_egitmen_paneli','agep_egitmen_paneli_shortcode');
add_shortcode('agep_sinav_formu','agep_sinav_formu_shortcode');
add_shortcode('agep_egitmen_sonuclari','agep_egitmen_sonuclari_shortcode');

function agep_ogrenci_paneli_shortcode(){
	if(!is_user_logged_in()) return '<p>Bu içeriği görüntülemek için lütfen giriş yapınız.</p>';
	
    $current_user = wp_get_current_user();
    $user_roles = (array) $current_user->roles;

	// KRİTİK DÜZELTME 1: N+1 Sorgu Problemini Çözme
	global $wpdb; 
	$table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
	$sonuclar = $wpdb->get_results($wpdb->prepare("SELECT sinav_id, sonuc_id FROM $table_name WHERE ogrenci_id = %d", $current_user->ID));
	
	$tamamlanan_sinavlar = [];
	if (!empty($sonuclar)) {
		foreach($sonuclar as $sonuc) {
			$tamamlanan_sinavlar[$sonuc->sinav_id] = $sonuc->sonuc_id;
		}
	}

    $args = [
        'post_type' => 'sinav',
        'posts_per_page' => -1,
		'post_status' => 'publish',
    ];

    $meta_query = [
        'relation' => 'OR',
        ['key' => '_sinav_hedef_rol', 'compare' => 'NOT EXISTS'],
        ['key' => '_sinav_hedef_rol', 'value' => 'a:0:{}', 'compare' => '='],
    ];
    foreach ($user_roles as $role) {
        $meta_query[] = ['key' => '_sinav_hedef_rol', 'value' => '"' . $role . '"', 'compare' => 'LIKE'];
    }
    $args['meta_query'] = $meta_query;

	$sinavlar = new WP_Query($args);

	$output = '<div class="agep-container"><h2>Sınavlarınız</h2>';
	if($sinavlar->have_posts()){
		$sinav_sayfasi_url = home_url('/sinav');
		$sonuc_sayfasi_url = home_url('/sonuclar');
		
		$output .= '<ul class="agep-exam-list">';
		while($sinavlar->have_posts()){
			$sinavlar->the_post();
			$sinav_id = get_the_ID();

			if(isset($tamamlanan_sinavlar[$sinav_id])){
				$sonuc_id = $tamamlanan_sinavlar[$sinav_id];
				$output .= '<li><span>' . get_the_title() . '</span>';
				$output .= '<span>(Tamamlandı) <a href="' . esc_url(add_query_arg('sonuc_id', $sonuc_id, $sonuc_sayfasi_url)) . '" class="agep-button">Sonucu Gör</a></span>';
				$output .= '</li>';
			} else {
				$output .= '<li><span>' . get_the_title() . '</span>';
				$output .= '<a href="' . esc_url(add_query_arg('sinav_id', $sinav_id, $sinav_sayfasi_url)) . '" class="agep-button">Sınava Başla</a>';
				$output .= '</li>';
			}
		}
		$output .= '</ul>';
	} else {
		$output .= '<p>Size atanmış aktif bir sınav bulunmamaktadır.</p>';
	}
	$output .= '</div>'; 
	wp_reset_postdata(); 
	return $output;
}
function agep_sinav_ekrani_shortcode(){
    nocache_headers(); 
    if(!is_user_logged_in()) return 'Bu sınavı görmek için giriş yapmalısınız.';
    if(!isset($_GET['sinav_id'])) return 'Hatalı istek.';
    
    $sinav_id = absint($_GET['sinav_id']); 
    $sinav = get_post($sinav_id);
    if(!$sinav || $sinav->post_type !== 'sinav') return 'Geçersiz sınav.';
    
    $uid = get_current_user_id();
    global $wpdb; $table = $wpdb->prefix . 'agep_sinav_sonuclari';
    
    if($wpdb->get_var($wpdb->prepare("SELECT sonuc_id FROM $table WHERE ogrenci_id = %d AND sinav_id = %d", $uid, $sinav_id))){
        return '<div class="agep-container"><p>Bu sınavı daha önce tamamladınız.</p></div>';
    }
    
    // Rol Kontrolü
    $hedef_roller = get_post_meta($sinav_id, '_sinav_hedef_rol', true);
    if( !empty($hedef_roller) && is_array($hedef_roller) ) {
        $user_roles = (array) wp_get_current_user()->roles;
        if ( empty(array_intersect( $user_roles, $hedef_roller )) ) return '<div class="agep-container">Yetkiniz yok.</div>';
    }

    // Süre Mantığı
    $sure_dk = intval(get_post_meta($sinav_id, '_sinav_sure', true));
    $kalan_saniye = 0;
    if ($sure_dk > 0) {
        $meta_key = "agep_sinav_{$sinav_id}_start";
        $baslangic = intval(get_user_meta($uid, $meta_key, true));
        if (!$baslangic) {
            $baslangic = current_time('timestamp');
            update_user_meta($uid, $meta_key, $baslangic);
        }
        $kalan_saniye = max(0, ($baslangic + ($sure_dk * 60)) - current_time('timestamp'));
    }

    // Kayıtlı Cevapları Getir (Autosave)
    $kayitli_cevaplar = get_user_meta($uid, 'agep_temp_answers_' . $sinav_id, true);
    if(!is_array($kayitli_cevaplar)) $kayitli_cevaplar = [];

    $sorular = get_post_meta($sinav_id, '_sinav_sorulari_data', true);
    if(empty($sorular)) return '<div class="agep-container">Soru yok.</div>';

    $output = '<div class="agep-container" style="position:relative;">';
    
    // Üst Panel (Sadece Başlık)
    $output .= '<div style="margin-bottom:20px; border-bottom:1px solid #eee; padding-bottom:10px;">';
    $output .= '<h1 style="margin:0; font-size:22px;">' . esc_html($sinav->post_title) . '</h1>';
    $output .= '</div>';
    
    if ($sure_dk > 0) {
        $output .= '<div id="agep-timer-banner" style="position:fixed;top:10px;right:10px;background:#d32f2f;color:#fff;padding:8px 12px;border-radius:4px;z-index:9999;font-weight:bold;font-size:14px;box-shadow:0 2px 5px rgba(0,0,0,0.2);">';
        $output .= '⏱️ <span id="agep-timer" data-remaining="' . intval($kalan_saniye) . '">...</span>';
        $output .= '</div>';
    }

    // Optik Form (Sidebar)
    $output .= '<div id="agep-optic-sidebar" class="agep-optic-sidebar">
        <h4>Optik Form</h4><div class="optic-grid"></div>
        <div style="margin-top:10px; font-size:11px; color:#666; line-height:1.4;">
        🔵: Dolu | 🟡: Boş<br>🟣: İncele (İşaretli)</div>
    </div>';

    // Form Başlangıcı
    $output .= '<form id="agep-sinav-formu" class="agep-form">
    <div id="agep-ajax-mesaj" class="agep-message"></div>
    <div id="agep-backup-area" style="display:none; margin-bottom:20px; padding:15px; background:#fff3e0; border:1px solid #ffb74d; border-radius:5px;"></div>'; 
    
    $output .= '<div class="agep-exam-pages">';
    $page_count = 1;
    $output .= '<div class="agep-page" data-page="1">'; 
    
    foreach($sorular as $index => $soru){
        // Bölüm Başlığı Kontrolü
        if( !empty($soru['bolum_basligi']) && $index > 0 ){
            $output .= '</div>'; $page_count++;
            $output .= '<div class="agep-page" data-page="'.$page_count.'">';
            $output .= '<h2 class="agep-section-title" style="border-bottom:2px solid #2196F3; color:#2196F3; padding-bottom:10px; margin-bottom:20px;">' . esc_html($soru['bolum_basligi']) . '</h2>';
        } elseif (!empty($soru['bolum_basligi']) && $index == 0) {
             $output .= '<h2 class="agep-section-title" style="border-bottom:2px solid #2196F3; color:#2196F3; padding-bottom:10px; margin-bottom:20px;">' . esc_html($soru['bolum_basligi']) . '</h2>';
        }

        // Soru Başlığı ve "Sonra İncele" Butonu
        $output .= '<fieldset class="agep-question-block" id="soru-block-'.$index.'">
        <legend><div style="display:flex; align-items:center; justify-content:space-between; width:100%;">
            <h3>' . ($index + 1) . '. Soru</h3>
            <button type="button" class="agep-mark-btn" data-index="'.$index.'" title="Bu soruyu sonra incelemek için işaretle" aria-label="Bu soruyu işaretle" aria-pressed="false" style="background:none; border:none; cursor:pointer; font-size:1.1em; color:#ccc; display:flex; align-items:center; gap:5px;">
                🏳️ <span style="font-size:12px; font-weight:normal;">İncele</span>
            </button>
        </div></legend>';

        // === SES OYNATICI ALANI ===
        if(isset($soru['ses_dosyasi']) && !empty($soru['ses_dosyasi'])){
            $audio_id = 'audio-' . $index;
            $btn_id = 'play-btn-' . $index;
            $output .= '<div class="agep-audio-player" style="margin-bottom:15px; padding:10px; background:#e8f5e9; border:1px solid #c8e6c9; border-radius:5px;">';
            $output .= '<audio id="'.$audio_id.'" src="'.esc_url($soru['ses_dosyasi']).'" style="display:none;"></audio>';
            $output .= '<button type="button" id="'.$btn_id.'" class="agep-button agep-listen-btn" onclick="agepToggleAudio(\''.$index.'\')" aria-label="Soruyu Dinle" style="background-color:#2e7d32;">🔊 Soruyu Dinle (Başlat)</button>';
            $output .= '</div>';
        }

        $output .= '<div class="soru-metni" style="font-size:1.15em; line-height:1.6; margin-bottom:15px;">' . wp_kses_post($soru['metin']) . '</div>';
        $output .= '<div class="cevap-siklari">';
        
        $siklar = ['a', 'b', 'c', 'd', 'e'];
        foreach($siklar as $sik){
            if( isset($soru['secenek_' . $sik]) && !empty($soru['secenek_' . $sik]) ){
                $checked = (isset($kayitli_cevaplar[$index]) && $kayitli_cevaplar[$index] == $sik) ? 'checked' : '';
                $sik_upper = strtoupper($sik); 
                
                // Sadeleştirilmiş Şık Satırı (Eleme butonu YOK)
                $output .= '<div class="agep-option-row">';
                $output .= '<input type="radio" id="c-'.$index.'-'.$sik.'" name="cevaplar[' . $index . ']" value="' . $sik . '" '.$checked.'>';
                $output .= '<label for="c-'.$index.'-'.$sik.'">';
                $output .= '<span class="sik-harfi">'.$sik_upper.'</span> ';
                $output .= '<span class="sik-metni">' . esc_html($soru['secenek_' . $sik]) . '</span>';
                $output .= '</label>';
                $output .= '</div>';
            }
        }
        // Boş Bırak
        $chk_bos = (!isset($kayitli_cevaplar[$index]) || $kayitli_cevaplar[$index] == 'bos') ? 'checked' : '';
        $output .= '<div class="agep-option-row" style="border:none; background:none; padding-left:0; margin-top:5px;">';
        $output .= '<input type="radio" id="c-'.$index.'-bos" name="cevaplar[' . $index . ']" value="bos" '.$chk_bos.'>';
        $output .= '<label for="c-'.$index.'-bos" style="color:#777; font-size:0.9em;">Bu soruyu boş bırak</label></div>';
        
        $output .= '</div></fieldset>';
    }
    $output .= '</div>'; // Pages end
    $output .= '</div>'; // Main container relative end

    // Navigasyon
    $output .= '<div class="agep-navigation">';
    $output .= '<button type="button" id="agep-prev-btn" class="agep-nav-btn">&laquo; Önceki</button>';
    $output .= '<button type="button" id="agep-next-btn" class="agep-nav-btn">Sonraki &raquo;</button>';
    $output .= '<button type="submit" id="agep-submit-btn" class="agep-nav-btn">Sınavı Bitir ✅</button>';
    $output .= '</div>';
    
    // Gizli Veriler
    $output .= '<input type="hidden" name="sinav_id" value="' . $sinav_id . '">';
    $output .= '<input type="hidden" name="analiz_sureler" id="analiz_sureler" value="">';
    $output .= '<input type="hidden" name="analiz_isaretliler" id="analiz_isaretliler" value="">';
    $output .= '</form>';

    ob_start();
    ?>
    <script type="text/javascript">
    // GLOBAL SES KONTROL FONKSİYONU
    function agepToggleAudio(id) {
        var audio = document.getElementById('audio-' + id);
        var btn = document.getElementById('play-btn-' + id);
        
        // Diğer tüm sesleri durdur
        var allAudios = document.querySelectorAll('audio');
        allAudios.forEach(function(el) {
            if(el.id !== 'audio-' + id) {
                el.pause();
                el.currentTime = 0;
                // Diğer butonları sıfırla
                var otherBtnId = el.id.replace('audio-', 'play-btn-');
                var otherBtn = document.getElementById(otherBtnId);
                if(otherBtn) otherBtn.innerHTML = '🔊 Soruyu Dinle (Başlat)';
            }
        });

        if (audio.paused) {
            audio.play();
            btn.innerHTML = '⏸️ Durdur';
        } else {
            audio.pause();
            btn.innerHTML = '▶️ Devam Et';
        }
        
        // Ses bittiğinde
        audio.onended = function() {
            btn.innerHTML = '🔄 Tekrar Dinle';
            audio.currentTime = 0;
        };
    }

    jQuery(document).ready(function($) {
        var currentPage = 1;
        var totalPages = $('.agep-page').length;
        var isSubmitting = false;
        var form = $("#agep-sinav-formu");
        var timerDisplay = $("#agep-timer");
        var remaining = parseInt(timerDisplay.data("remaining"), 10) || 0;
        var sinavID = <?php echo $sinav_id; ?>;
        
        // --- DEMİR KALKAN (YEREL YEDEKLEME) ---
        var storageKey = 'agep_backup_' + sinavID;
        // Sayfa açıldığında yerel yedeği kontrol et (Gelişmiş senaryolarda buradan restore edilebilir)
        if(localStorage.getItem(storageKey)) console.log("Yedek mevcut.");

        function saveToLocal() {
            var data = form.serializeArray();
            localStorage.setItem(storageKey, JSON.stringify(data));
        }

        // --- SÜRE ANALİZİ (GİZLİ SAYAÇ) ---
        var pageTimes = {}; 
        var pageStartTime = Date.now();
        
        function trackTime() {
            var now = Date.now();
            var diff = (now - pageStartTime) / 1000;
            if(!pageTimes[currentPage]) pageTimes[currentPage] = 0;
            pageTimes[currentPage] += diff;
            pageStartTime = now;
            $('#analiz_sureler').val(JSON.stringify(pageTimes));
        }

        // --- NAVİGASYON ---
        function updateNav() {
            // Sayfa değişince çalan sesi durdur
            $('audio').each(function(){ this.pause(); });
            
            trackTime(); 
            $('.agep-page').hide();
            $('.agep-page[data-page="'+currentPage+'"]').fadeIn(300);
            
            if(currentPage <= 1) $('#agep-prev-btn').css('visibility', 'hidden');
            else $('#agep-prev-btn').css('visibility', 'visible');
            if(currentPage === totalPages) { $('#agep-next-btn').hide(); $('#agep-submit-btn').show(); } 
            else { $('#agep-next-btn').show(); $('#agep-submit-btn').hide(); }
            $('html, body').animate({ scrollTop: $(".agep-container").offset().top - 70 }, 400);
            saveToLocal();
        }
        $('#agep-next-btn').click(function(){ if(currentPage < totalPages) { currentPage++; updateNav(); } });
        $('#agep-prev-btn').click(function(){ if(currentPage > 1) { currentPage--; updateNav(); } });
        updateNav();

        // --- İŞARETLEME (BAYRAK) ---
        var markedQuestions = [];
        $('.agep-mark-btn').click(function(){
            var btn = $(this);
            var qIdx = btn.data('index');
            
            if(markedQuestions.includes(qIdx)){
                markedQuestions = markedQuestions.filter(item => item !== qIdx);
                btn.css('color', '#ccc').attr('aria-pressed', 'false');
                $('#dot-'+qIdx).removeClass('marked');
            } else {
                markedQuestions.push(qIdx);
                btn.css('color', '#9c27b0').attr('aria-pressed', 'true'); 
                $('#dot-'+qIdx).addClass('marked');
            }
            $('#analiz_isaretliler').val(JSON.stringify(markedQuestions));
        });

        // --- OPTİK FORM ---
        function initOptic() {
            var grid = $('.optic-grid');
            grid.empty();
            $('.agep-question-block').each(function(i){
                var qIdx = i;
                var dot = $('<div class="optic-dot" id="dot-'+qIdx+'">'+(qIdx+1)+'</div>');
                dot.click(function(){
                    var targetPage = $('#soru-block-'+qIdx).closest('.agep-page').data('page');
                    if(currentPage !== targetPage) { trackTime(); currentPage = targetPage; updateNav(); }
                    setTimeout(function(){ $('html, body').animate({ scrollTop: $('#soru-block-'+qIdx).offset().top - 100 }, 500); }, 100);
                });
                grid.append(dot);
            });
            refreshOpticColors();
        }
        function refreshOpticColors() {
            $('.agep-question-block').each(function(i){
                var val = $(this).find('input:checked').val();
                var dot = $('#dot-'+i);
                dot.removeClass('filled empty');
                if(val && val !== 'bos') dot.addClass('filled');
                else if(val === 'bos') dot.addClass('empty');
            });
            saveToLocal(); 
        }
        $('input[type="radio"]').on('change', refreshOpticColors);
        initOptic();

        // --- TIMER & GÜVENLİ AUTOSAVE ---
        if(remaining > 0){
            var timerInt = setInterval(function() {
                remaining--;
                var m = Math.floor(remaining / 60); var s = remaining % 60;
                timerDisplay.text((m<10?"0"+m:m) + ":" + (s<10?"0"+s:s));
                if (remaining <= 0) {
                    clearInterval(timerInt);
                    if (!isSubmitting) { 
                        alert("Süre doldu! Otomatik gönderiliyor...");
                        submitExamWithSafety();
                    }
                }
            }, 1000);
        }

        // AKILLI AUTOSAVE (Değişiklik varsa kaydet)
        var lastData = form.serialize();
        setInterval(function(){
            if(isSubmitting || (remaining <= 0 && remaining !== 0)) return;
            trackTime(); 
            var currData = form.serialize();
            if(currData === lastData) return; // Değişiklik yok, sunucuyu yorma
            lastData = currData;
            $.post(agep_ajax_obj.ajax_url, currData + "&action=agep_autosave_exam&nonce=" + agep_ajax_obj.autosave_nonce);
        }, 20000); // 20 saniyede bir kontrol et

        // --- GÖNDERME FONKSİYONLARI ---
        function submitExamWithSafety() {
            if (isSubmitting) return; isSubmitting = true;
            trackTime(); 
            var btn = $("#agep-submit-btn"), msg = $("#agep-ajax-mesaj");
            btn.prop("disabled", true).text("Gönderiliyor...");
            msg.text("Sonuçlar işleniyor...").removeClass("error success").addClass("info").show();
            
            $.post(agep_ajax_obj.ajax_url, form.serialize() + "&action=agep_submit_exam&nonce=" + agep_ajax_obj.nonce, function(response) {
                if (response.success) {
                    localStorage.removeItem(storageKey); // Temizlik
                    msg.text("Başarılı!").addClass("success");
                    window.location.href = response.data.redirect_url;
                } else { handleError(response.data.message); }
            }).fail(function(xhr, status, error) { handleError("Sunucu bağlantı hatası: " + error); });
        }

        function handleError(errorMsg) {
            var msg = $("#agep-ajax-mesaj");
            var btn = $("#agep-submit-btn");
            var backupArea = $("#agep-backup-area");
            
            msg.html("⚠️ <b>HATA:</b> " + errorMsg + "<br>Endişelenmeyin, cevaplarınız tarayıcıda güvende.").addClass("error");
            btn.prop("disabled", false).text("Tekrar Dene");
            isSubmitting = false;

            // Yedek İndirme Butonunu Göster
            var backupData = JSON.stringify(form.serializeArray());
            backupArea.show().html(`
                <h4>⚠️ Bağlantı Sorunu</h4>
                <p>İnternetiniz gitmiş olabilir. "Tekrar Dene"ye basın. Sorun devam ederse yedeği indirin:</p>
                <button type="button" class="agep-button" style="background:#ff9800;" onclick="downloadBackup()">📂 Yedeği İndir (Güvenli)</button>
            `);
            
            window.downloadBackup = function() {
                var blob = new Blob([backupData], {type: "application/json"});
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a'); a.href = url; a.download = "sinav_yedegi_" + sinavID + ".json";
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
            };
        }

        form.on("submit", function(e) {
            e.preventDefault(); 
// GELİŞMİŞ UYARI SİSTEMİ
            if(markedQuestions.length > 0) {
                // 1. İndeksleri Soru Numarasına Çevir (0 -> 1) ve Sayısal Olarak Sırala
                var qNumbers = markedQuestions.map(function(idx) {
                    return parseInt(idx) + 1;
                }).sort(function(a, b) { return a - b; });

                // 2. Mesajı Oluştur
                var msg = "⚠️ DİKKAT! Kontrol Etmediğiniz Sorular Var\n\n";
                msg += "Şu soruları 'Sonra İncele' olarak işaretlediniz:\n";
                msg += "Soru No: " + qNumbers.join(", ") + "\n\n";
                msg += "Bu sorulara dönüp bakmak ister misiniz? Bitirmek için 'Tamam', dönmek için 'İptal'e basın.";

                // 3. Kullanıcıya Sor
                if(!confirm(msg)) {
                    return; // İptal'e basarsa gönderme işlemini durdur
                }
            }
            submitExamWithSafety();
        });
    });
    </script>
    <?php
    $output .= ob_get_clean();
    $output .= '</div>';
    return $output;
}
function agep_sonuc_ekrani_shortcode(){
	if(!is_user_logged_in()){ return 'Sonuçları görmek için giriş yapmalısınız.'; }
	if(!isset($_GET['sonuc_id'])){ return 'Hatalı istek.'; }
global $wpdb; $sonuc_id = absint($_GET['sonuc_id']); $current_user_id = get_current_user_id();
$table_name = $wpdb->prefix . 'agep_sinav_sonuclari'; $sonuc = null;
if ( current_user_can('manage_options') || current_user_can('edit_others_posts') || current_user_can('edit_sinavs') ) {
    $sonuc = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM $table_name WHERE sonuc_id = %d", $sonuc_id ) );
} else {
    $sonuc = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM $table_name WHERE sonuc_id = %d AND ogrenci_id = %d", $sonuc_id, $current_user_id ) );
}
if ( ! $sonuc ) {
    return '<div class="agep-container"><p>Bu sonuca erişim yetkiniz yok veya sonuç bulunamadı.</p></div>';
}
$sinav = get_post($sonuc->sinav_id); $ogrenci = get_userdata($sonuc->ogrenci_id);

	$ogrenci_cevaplari = json_decode($sonuc->cevaplar, true);
	$sorular = get_post_meta($sinav->ID, '_sinav_sorulari_data', true);
	$output = '<div class="agep-container"><h1>Sınav Sonuç Belgesi</h1>';
	$output .= '<h2>' . esc_html($sinav->post_title) . '</h2>';
	$output .= '<p><strong>Öğrenci:</strong> ' . esc_html($ogrenci->display_name) . '<br><strong>Tarih:</strong> ' . date_i18n(get_option('date_format'), strtotime($sonuc->tarih)) . '</p>';
	$output .= '<div class="agep-summary-box"><h3>Sınav Özeti</h3><ul><li><strong>Doğru Sayısı:</strong> ' . $sonuc->dogru_sayisi . '</li><li><strong>Yanlış Sayısı:</strong> ' . $sonuc->yanlis_sayisi . '</li><li><strong>Boş Sayısı:</strong> ' . $sonuc->bos_sayisi . '</li><li><strong>Net Puan:</strong> ' . number_format($sonuc->net_puan, 2) . '</li></ul></div><hr>';
	$output .= '<h3>Detaylı Analiz</h3>';
	if(!is_array($sorular)) $sorular = [];
	foreach($sorular as $index => $soru){
		$soru_numarasi = $index + 1; $dogru_cevap = isset($soru['dogru_cevap']) ? $soru['dogru_cevap'] : '';
		$ogrenci_cevabi = isset($ogrenci_cevaplari[$index]) ? strtoupper($ogrenci_cevaplari[$index]) : 'BOŞ';
		$output .= '<div class="agep-analysis-block">';
		$output .= '<h4>' . $soru_numarasi . '. Soru:</h4> <div>' . wp_kses_post($soru['metin']) . '</div>';
		$output .= '<p>Sizin Cevabınız: <strong>' . $ogrenci_cevabi . '</strong><br>Doğru Cevap: <strong>' . strtoupper($dogru_cevap) . '</strong></p>';
		
        $output .= '<div class="agep-all-options" style="margin-top:15px; padding:10px; border:1px solid #eee;"><h4>Sorunun Şıkları:</h4>';
        $siklar = ['a', 'b', 'c', 'd', 'e'];
        foreach ($siklar as $sik) {
            if (isset($soru['secenek_' . $sik]) && !empty($soru['secenek_' . $sik])) {
                $output .= '<p style="margin: 5px 0;"><strong>' . strtoupper($sik) . ')</strong> ' . esc_html($soru['secenek_' . $sik]) . '</p>';
            }
        }
        $output .= '</div>';

        if($ogrenci_cevabi != strtoupper($dogru_cevap) && $ogrenci_cevabi != 'BOŞ'){
			$aciklama = isset($soru['aciklama']) ? $soru['aciklama'] : '';
			if(!empty($aciklama)){
				$output .= '<div class="agep-explanation-box"><strong>Açıklama:</strong> ' . wpautop(wp_kses_post($aciklama)) . '</div>';
			}
		}
		$output .= '</div>';
	}
	$output .= '</div>';
	return $output;
}

function agep_egitmen_paneli_shortcode(){
	if(!is_user_logged_in() || !current_user_can('edit_sinavs')){
		return '<div class="agep-container"><p>Bu sayfayı görüntüleme yetkiniz yok.</p></div>';
	}
	$user = wp_get_current_user();
	$output = '<div class="agep-container">';
	$output .= '<h1>Eğitmen Paneli</h1>';
	$output .= '<p>Hoş geldiniz, ' . esc_html($user->display_name) . '.</p>';
	$output .= '<h2>Sınav Yönetimi</h2>';
	$output .= '<ul class="agep-exam-list">';
	$output .= '<li><span>Yeni bir sınav oluşturun.</span><a href="' . home_url('/sinav-yonetimi/') . '" class="agep-button">Yeni Sınav Oluştur</a></li>';
	$output .= '<li><span>Mevcut sınavları düzenleyin veya sonuçlarını görüntüleyin.</span><a href="' . home_url('/egitmen-sonuclari/') . '" class="agep-button">Sınavları Yönet</a></li>';
	$output .= '</ul></div>';
	return $output;
}

function agep_sinav_formu_shortcode(){
	if(!current_user_can('edit_sinavs')) return '<div class="agep-container"><p>Bu sayfayı görüntüleme yetkiniz yok.</p></div>';
	$sinav_id = isset($_GET['sinav_id']) ? absint($_GET['sinav_id']) : 0; $sinav = null; $post_title = ''; $post_content = '';
	if($sinav_id > 0){
		$sinav = get_post($sinav_id);
		if(!$sinav || !current_user_can('edit_post', $sinav_id)){
			return '<div class="agep-container"><p>Bu sınavı düzenleme yetkiniz yok.</p></div>';
		}
		$post_title = $sinav->post_title; $post_content = $sinav->post_content;
	}
	$editor_id = 'agep_post_content'; $editor_settings = ['textarea_name' => 'post_content', 'media_buttons' => true, 'textarea_rows' => 10, 'teeny' => false];
	ob_start();
	echo '<div class="agep-container agep-form"><h1>' . ($sinav_id > 0 ? 'Sınav Düzenle' : 'Yeni Sınav Oluştur') . '</h1><form id="agep-frontend-exam-form"><div id="agep-ajax-mesaj" role="alert" class="agep-message"></div><p><label for="post_title">Sınav Başlığı</label><input type="text" name="post_title" id="post_title" value="' . esc_attr($post_title) . '" required></p><p><label for="' . $editor_id . '">Sınav Açıklaması</label>';
	wp_editor($post_content, $editor_id, $editor_settings);
	echo '</p><hr><h3>Sınav Ayarları</h3>';
	agep_sinav_ayarlari_meta_box_html($sinav);
	echo '<hr><h3>Sorular</h3>';
	agep_sinav_sorulari_meta_box_html($sinav);
	echo '<input type="hidden" name="post_id" value="' . $sinav_id . '">';
	wp_nonce_field('agep_sinav_save_data', 'agep_sinav_nonce', false);
	echo '<button type="submit" class="agep-button">Sınavı Kaydet</button></form>';
	echo agep_get_repeater_js_template(); ?>
<script>jQuery(document).ready(function($){$("#agep-frontend-exam-form").on("submit",function(e){e.preventDefault();var form=$(this);var btn=form.find('button[type="submit"]');var msg=$("#agep-ajax-mesaj"); if (typeof tinymce !== 'undefined' && tinymce.get('agep_post_content')) { tinymce.get('agep_post_content').save(); } btn.prop("disabled",true).text("Kaydediliyor...");msg.text("Lütfen bekleyin...").removeClass("error success").addClass("info").show();$.post(agep_ajax_obj.ajax_url,form.serialize()+"&action=agep_save_exam_from_frontend&nonce="+agep_ajax_obj.nonce,function(r){if(r.success){msg.text(r.data.message).removeClass("info error").addClass("success");if(r.data.redirect_url){setTimeout(function(){window.location.href=r.data.redirect_url;},1500);}}else{msg.text("Hata: "+r.data.message).removeClass("info success").addClass("error");btn.prop("disabled",false).text("Sınavı Kaydet");}});});});</script>
<?php
	return ob_get_clean();
}

function agep_egitmen_sonuclari_shortcode(){
	if(!current_user_can('edit_sinavs')) return '<div class="agep-container"><p>Bu sayfayı görüntüleme yetkiniz yok.</p></div>';

	global $wpdb;
	$user_id = get_current_user_id();
	$output = '<div class="agep-container">';

	if(isset($_GET['sinav_id'])){
		$sinav_id = absint($_GET['sinav_id']);
		if(!current_user_can('edit_post', $sinav_id)){
			return '<div class="agep-container"><p>Bu sınavın sonuçlarını görme yetkiniz yok.</p></div>';
		}
		$sinav = get_post($sinav_id);
		$table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
		$sonuclar = $wpdb->get_results($wpdb->prepare("SELECT * FROM $table_name WHERE sinav_id = %d ORDER BY tarih DESC", $sinav_id));
		$sorular = get_post_meta($sinav_id, '_sinav_sorulari_data', true);

		$output .= '<h1>' . esc_html($sinav->post_title) . ' Sonuçları</h1>';
		$output .= '<p><a href="' . home_url('/egitmen-sonuclari/') . '">&laquo; Sınav Listesine Geri Dön</a></p>';

		if(empty($sonuclar)){
			$output .= '<p>Bu sınava henüz giren olmamış.</p>';
		} else {
			$katilimci_sayisi = count($sonuclar);
			$net_puanlar = array_map(function($s){ return (float)$s->net_puan; }, $sonuclar);
			$stats = agep_stats_basic($net_puanlar);
			list($ranges, $hist) = agep_histogram($net_puanlar, 8);
			$items = agep_build_item_analysis($sorular, $sonuclar);

			$export_nonce = wp_create_nonce('agep_export_nonce_' . $sinav_id);
			$export_results_link = add_query_arg(['action' => 'agep_export_csv', 'sinav_id' => $sinav_id, 'nonce' => $export_nonce], home_url('/'));
			$export_analysis_link = add_query_arg(['action' => 'agep_export_csv', 'type' => 'analysis', 'sinav_id' => $sinav_id, 'nonce' => $export_nonce], home_url('/'));

			$output .= '<div class="agep-summary-box" style="margin-bottom: 20px;"><h3>Sınav İstatistikleri</h3><ul>';
			$output .= '<li><strong>Katılımcı Sayısı:</strong> ' . $katilimci_sayisi . '</li>';
			$output .= '<li><strong>Ortalama:</strong> ' . number_format($stats['mean'], 2) . '</li>';
			$output .= '<li><strong>Medyan:</strong> ' . number_format($stats['median'], 2) . '</li>';
			$output .= '<li><strong>Standart Sapma:</strong> ' . number_format($stats['std'], 2) . '</li>';
			$output .= '<li><strong>En Yüksek:</strong> ' . number_format($stats['max'], 2) . '</li>';
			$output .= '<li><strong>En Düşük:</strong> ' . number_format($stats['min'], 2) . '</li>';
			$output .= '</ul><div class="agep-button-group"><a href="'.esc_url($export_results_link).'" class="agep-button">Sonuçları Dışa Aktar (CSV)</a> ';
			$output .= '<a href="'.esc_url($export_analysis_link).'" class="agep-button">Soru Analizi (CSV)</a></div></div>';

			if (!empty($hist) && !empty($ranges)) {
				$output .= '<h3>Not Dağılımı (Histogram)</h3><table class="agep-results-table"><thead><tr><th>Aralık</th><th>Adet</th></tr></thead><tbody>';
				foreach ($hist as $i => $cnt) {
					$r = $ranges[$i];
					$output .= '<tr><td>' . number_format($r[0],2) . ' - ' . number_format($r[1],2) . '</td><td>' . intval($cnt) . '</td></tr>';
				}
				$output .= '</tbody></table>';
			}

			if (is_array($items) && !empty($items)) {
				$output .= '<h3>Soru Bazlı Analiz</h3><table class="agep-results-table"><thead><tr><th>#</th><th>Doğru %</th><th>Doğru</th><th>Yanlış</th><th>Boş</th><th>Doğru Cevap</th><th>Soru</th></tr></thead><tbody>';
				$toplam = max(1, $katilimci_sayisi);
				foreach ($items as $i => $row) {
					$s = isset($sorular[$i]) ? $sorular[$i] : [];
					$pct = ($row['dogru'] / $toplam) * 100;
					$output .= '<tr>';
					$output .= '<td>' . ($i+1) . '</td>';
					$output .= '<td>' . number_format($pct, 2) . '%</td>';
					$output .= '<td>' . intval($row['dogru']) . '</td>';
					$output .= '<td>' . intval($row['yanlis']) . '</td>';
					$output .= '<td>' . intval($row['bos']) . '</td>';
					$output .= '<td>' . (isset($s['dogru_cevap']) ? strtoupper($s['dogru_cevap']) : '') . '</td>';
					$output .= '<td>' . (isset($s['metin']) ? esc_html(wp_strip_all_tags($s['metin'])) : '') . '</td>';
					$output .= '</tr>';
				}
				$output .= '</tbody></table>';
			}

			$output .= '<h3>Katılımcı Sonuçları</h3><table class="agep-results-table"><thead><tr><th>Öğrenci</th><th>Tarih</th><th>Doğru</th><th>Yanlış</th><th>Boş</th><th>Net Puan</th><th>Detay</th></tr></thead><tbody>';
			foreach($sonuclar as $sonuc){
				$ogrenci = get_userdata($sonuc->ogrenci_id);
				$detay_link = add_query_arg('sonuc_id', $sonuc->sonuc_id, home_url('/sonuclar'));
				$output .= '<tr><td>' . esc_html($ogrenci ? $ogrenci->display_name : '-') . '</td><td>' . date_i18n(get_option('date_format'), strtotime($sonuc->tarih)) . '</td><td>' . $sonuc->dogru_sayisi . '</td><td>' . $sonuc->yanlis_sayisi . '</td><td>' . $sonuc->bos_sayisi . '</td><td>' . number_format($sonuc->net_puan, 2) . '</td><td><a href="' . esc_url($detay_link) . '" target="_blank" class="agep-button">Karneye Git</a></td></tr>';
			}
			$output .= '</tbody></table>';
		}
	} else {
		$output .= '<h1>Sınavlarım</h1><p>Sonuçlarını veya detaylarını görmek istediğiniz sınavı seçin.</p>';
		$query_args = ['post_type' => 'sinav', 'posts_per_page' => -1, 'post_status' => 'publish'];
if (!current_user_can('manage_options') && !current_user_can('edit_sinavs')) {
    $query_args['author'] = $user_id;
}

		$sinavlar = new WP_Query($query_args);

		if(!$sinavlar->have_posts()){
			$output .= '<p>Henüz hiç sınav oluşturmamışsınız.</p>';
		} else {
			$output .= '<ul class="agep-exam-list">';
			while($sinavlar->have_posts()){
				$sinavlar->the_post();
				$sinav_id = get_the_ID();
				$edit_link = add_query_arg('sinav_id', $sinav_id, home_url('/sinav-yonetimi/'));
				$results_link = add_query_arg('sinav_id', $sinav_id, home_url('/egitmen-sonuclari/'));
				$output .= '<li id="sinav-li-'.$sinav_id.'"><span>'.get_the_title().'</span><div class="agep-button-group">';
				$output .= '<a href="'.esc_url($edit_link).'" class="agep-button">Düzenle</a> ';
				$output .= '<a href="'.esc_url($results_link).'" class="agep-button">Sonuçları Gör</a> ';
				$output .= '<a href="#" class="agep-button agep-button-delete agep-sinav-sil-btn" data-sinav-id="'.$sinav_id.'">Sil</a>';
				$output .= '</div></li>';
			}
			$output .= '</ul>';
		}
		wp_reset_postdata();
	}

	$output .= '</div>';
	ob_start(); ?>
	<script>
	jQuery(document).ready(function($) {
		$('.agep-sinav-sil-btn').on('click', function(e) {
			e.preventDefault();
			var button = $(this);
			var sinavId = button.data('sinav-id');
			if (confirm('Bu sınavı ve tüm sonuçlarını kalıcı olarak silmek istediğinize emin misiniz? Bu işlem geri alınamaz.')) {
				button.text('Siliniyor...');
				$.post(agep_ajax_obj.ajax_url, {
					action: 'agep_delete_exam',
					nonce: agep_ajax_obj.delete_nonce,
					sinav_id: sinavId
				}, function(response) {
					if (response.success) {
						$('#sinav-li-' + sinavId).fadeOut(500, function() { $(this).remove(); });
						alert(response.data.message);
					} else {
						alert('Hata: ' + response.data.message);
						button.text('Sil');
					}
				});
			}
		});
	});
	</script>
	<?php
	$output .= ob_get_clean();
	return $output;
}

function agep_admin_results_page_html(){
	global $wpdb; $table_name = $wpdb->prefix . 'agep_sinav_sonuclari';
	echo '<div class="wrap"><h1>Sınav Sonuçları (Yönetici Görünümü)</h1>';
	$user = wp_get_current_user();
	if(isset($_GET['sinav_id'])){
		$sinav_id = absint($_GET['sinav_id']);
		if(in_array('egitmen',(array)$user->roles) && get_post_field('post_author',$sinav_id) != $user->ID && !current_user_can('manage_options')){wp_die('Bu sınavın sonuçlarını görme yetkiniz yok.');}
		$sinav=get_post($sinav_id);$sonuclar=$wpdb->get_results($wpdb->prepare("SELECT * FROM $table_name WHERE sinav_id = %d ORDER BY tarih DESC",$sinav_id));
		echo '<h2>'.esc_html($sinav->post_title).' Sınavı Sonuçları</h2>';
		echo '<a href="'.admin_url('edit.php?post_type=sinav&page=agep-sinav-sonuclari').'">&laquo; Tüm Sınavlara Geri Dön</a>';
		if(empty($sonuclar)){
			echo '<p>Bu sınava henüz giren olmamış.</p>';
		}else{
			echo '<table class="wp-list-table widefat fixed striped">';
			echo '<thead><tr><th>Öğrenci</th><th>Tarih</th><th>Doğru</th><th>Yanlış</th><th>Boş</th><th>Net Puan</th><th>Detay</th></tr></thead>';
			echo '<tbody>';
			foreach($sonuclar as $sonuc){
				$ogrenci=get_userdata($sonuc->ogrenci_id);
				$detay_link=add_query_arg('sonuc_id',$sonuc->sonuc_id,home_url('/sonuclar'));
				echo '<tr>';
				echo '<td>'.esc_html($ogrenci?$ogrenci->display_name:'-').'</td>';
				echo '<td>'.date_i18n(get_option('date_format'),strtotime($sonuc->tarih)).'</td>';
				echo '<td>'.$sonuc->dogru_sayisi.'</td><td>'.$sonuc->yanlis_sayisi.'</td><td>'.$sonuc->bos_sayisi.'</td><td>'.number_format($sonuc->net_puan,2).'</td><td><a href="'.esc_url($detay_link).'" target="_blank">Karneye Git</a></td></tr>';
			}
			echo '</tbody></table>';
		}
	}else{
		echo '<p>Sonuçlarını görmek istediğiniz sınavı seçin.</p>';
		$query_args=['post_type'=>'sinav', 'posts_per_page' => -1, 'post_status' => 'publish'];
		if(in_array('egitmen',(array)$user->roles) && !current_user_can('manage_options')){$query_args['author']=$user->ID;}
		$sinavlar=get_posts($query_args);
		if(empty($sinavlar)){
			echo '<p>Henüz hiç sınav oluşturulmamış.</p>';
		}else{
			echo '<ul>';
			foreach($sinavlar as $sinav){
				$link=add_query_arg('sinav_id',$sinav->ID,admin_url('edit.php?post_type=sinav&page=agep-sinav-sonuclari'));
				echo '<li><h3><a href="'.esc_url($link).'">'.esc_html($sinav->post_title).'</a></h3></li>';
			}
			echo '</ul>';
		}
	}
	echo '</div>';
}