bl_info = {
    "name": "ToPu_RemapFramerateAddon",
    "author": "http4211",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "Dope Sheet / Graph Editor / NLA Editor > Header",
    'tracker_url': 'https://github.com/http4211/ToPu_RemapFramerateAddon',
    "description": "Remap keyframes, markers, and frame range when changing framerate",
    "category": "Animation",
}

import bpy


class FRAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    show_format_ui: bpy.props.BoolProperty(
        name="Show in Output",
        default=True
    )
    show_header_ui: bpy.props.BoolProperty(
        name="Show in Header",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Remap Framerate UI Display location of")
        row = layout.row()
        row.prop(self, "show_format_ui")
        row.prop(self, "show_header_ui")

        if not self.show_format_ui and not self.show_header_ui:
            layout.label(text="Please turn on at least one of them.", icon="ERROR")




# プリセットリスト
FRAMERATE_PRESETS = [
    ('23.98', "23.98 fps", "23.98 frames per second"),
    ('24', "24 fps", "24 frames per second"),
    ('25', "25 fps", "25 frames per second"),
    ('29.97', "29.97 fps", "29.97 frames per second"),
    ('30', "30 fps", "30 frames per second"),
    ('48', "48 fps", "48 frames per second"),
    ('50', "50 fps", "50 frames per second"),
    ('59.94', "59.94 fps", "59.94 frames per second"),
    ('60', "60 fps", "60 frames per second"),
    ('72', "72 fps", "72 frames per second"),
    ('120', "120 fps", "120 frames per second"),
    ('240', "240 fps", "240 frames per second"),
    ('CUSTOM', "Custom", "Custom framerate")
]

_last_fps = None

def framerate_timer():
    global _last_fps
    scene = bpy.context.scene
    fps_real = round(scene.render.fps / scene.render.fps_base, 2)
    if _last_fps is None:
        _last_fps = fps_real
    if fps_real != _last_fps:
        update_framerate_preset(scene)
        _last_fps = fps_real
    return 0.5  # 0.5秒ごとにチェック

class FR_OT_Remap_Framerate(bpy.types.Operator):
    bl_idname = "fr.remap_framerate"
    bl_label = "Remap Framerate"
    bl_description = "Remap keyframes, markers, and frame range when changing framerate"
    bl_options = {'UNDO', 'REGISTER'}

    remap_marker: bpy.props.BoolProperty(default=True)
    remap_keyframes: bpy.props.BoolProperty(default=True)
    remap_frame_range: bpy.props.BoolProperty(default=True)
    subframe: bpy.props.BoolProperty(default=True)
    remap_manual_frame_range: bpy.props.BoolProperty(default=True)

    def draw(self, context):
        layout = self.layout
        layout.label(text="This is a Destructive Operator", icon="ERROR")
        layout.label(text="Please Backup Before Proceeding", icon="INFO")
        layout.prop(self, "remap_marker", text="Markers")
        layout.prop(self, "remap_keyframes", text="Keyframes")
        layout.prop(self, "remap_manual_frame_range", text="Action Manual Frame Range")
        layout.prop(self, "remap_frame_range", text="Frame Range")
        layout.prop(self, "subframe", text="Subframe")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scn = context.scene
        old = scn.render.fps / scn.render.fps_base
        preset = context.scene.framerate_preset
        if preset != 'CUSTOM':
            new = float(preset)
        else:
            new = context.scene.fr_target_fps
        use_subframe = not self.subframe

        if abs(old - new) < 0.001:
            self.report({'INFO'}, "Framerate is already the target value.")
            return {'CANCELLED'}

        rate = old / new

        if self.remap_keyframes:
            for action in bpy.data.actions:
                for fc in action.fcurves:
                    for kf in fc.keyframe_points:
                        if use_subframe:
                            kf.co.x = int(kf.co.x / rate)
                            kf.handle_left[0] = int(kf.handle_left[0] / rate)
                            kf.handle_right[0] = int(kf.handle_right[0] / rate)
                        else:
                            kf.co.x = kf.co.x / rate
                            kf.handle_left[0] = kf.handle_left[0] / rate
                            kf.handle_right[0] = kf.handle_right[0] / rate

        if self.remap_marker:
            for scene in bpy.data.scenes:
                for tm in scene.timeline_markers:
                    tm.frame = int(tm.frame / rate)

            for action in bpy.data.actions:
                for pm in action.pose_markers:
                    pm.frame = int(pm.frame / rate)

        if self.remap_manual_frame_range:
            for action in bpy.data.actions:
                action.frame_start = int(action.frame_start / rate)
                action.frame_end = int(action.frame_end / rate)

        if self.remap_frame_range:
            context.scene.frame_start = int(context.scene.frame_start / rate)
            context.scene.frame_end = int(context.scene.frame_end / rate)

        # FPSとFPSベースのプリセット辞書
        preset_fps_settings = {
            '23.98': (24000, 1001),
            '29.97': (30000, 1001),
            '59.94': (5994, 100),
            '24': (24, 1),
            '25': (25, 1),
            '30': (30, 1),
            '50': (50, 1),
            '60': (60, 1),
            '120': (120, 1),
            '240': (240, 1),
            '48': (48, 1),
            '72': (72, 1),
        }

        if preset in preset_fps_settings:
            fps_num, fps_base = preset_fps_settings[preset]
            scn.render.fps = fps_num
            scn.render.fps_base = fps_base
        else:
            # カスタム時
            scn.render.fps = int(new)
            scn.render.fps_base = 1.0
        self.report({'INFO'}, f"Remapped framerate from {old} to {new}.")
        return {'FINISHED'}

class FR_PT_remap_in_output_format_like(bpy.types.Panel):
    bl_label = "Remap Framerate"
    bl_idname = "FR_PT_remap_in_output_format_like"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"
    bl_parent_id = "RENDER_PT_format"  # 親をFormatにすることで「中っぽく」表示される

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        return prefs.show_format_ui

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        fps_real = round(scene.render.fps / scene.render.fps_base, 2)
        target_fps = float(scene.fr_target_fps) if scene.framerate_preset == 'CUSTOM' else float(scene.framerate_preset)
        is_mismatch = abs(fps_real - target_fps) > 0.01

        box = layout.box()
        box_col = box.column(align=True)
        box_col.alert = is_mismatch
        box_col.prop(scene, "framerate_preset", text="Preset")
        if scene.framerate_preset == 'CUSTOM':
            box_col.prop(scene, "fr_target_fps", text="Custom FPS")

        box_col.separator()

        row = box_col.row()
        row.alert = is_mismatch
        row.operator("fr.remap_framerate", icon="TIME")




class FR_PT_Remap_Framerate_Panel(bpy.types.Panel):
    bl_label = "Remap Framerate"
    bl_idname = "FR_PT_remap_framerate_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.operator("fr.remap_framerate", icon="TIME")

def dopesheet_menu(self, context):
    prefs = bpy.context.preferences.addons[__name__].preferences
    if not prefs.show_header_ui:
        return

    layout = self.layout
    scene = context.scene

    fps_real = round(scene.render.fps / scene.render.fps_base, 2)
    target_fps = float(scene.fr_target_fps) if scene.framerate_preset == 'CUSTOM' else float(scene.framerate_preset)

    row = layout.row(align=True)
    split = row.split(factor=0.7, align=True)

    split_left = split.row(align=True)
    if abs(fps_real - target_fps) > 0.01:
        split_left.alert = True
    split_left.prop(scene, "framerate_preset", text="")
    if scene.framerate_preset == 'CUSTOM':
        split_left.prop(scene, "fr_target_fps", text="")

    split_right = split.row(align=True)
    if abs(fps_real - target_fps) > 0.01:
        split_right.alert = True
    split_right.operator("fr.remap_framerate", text="", icon="SCENE_DATA")




def graph_editor_menu(self, context):
    dopesheet_menu(self, context)

def nla_editor_menu(self, context):
    dopesheet_menu(self, context)

class FR_MT_FramerateMenu(bpy.types.Menu):
    bl_label = "Framerate Menu"
    bl_idname = "FR_MT_framerate_menu"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        for (value, name, _) in FRAMERATE_PRESETS:
            op = layout.operator("fr.set_framerate_preset", text=name)
            op.preset_value = value




def tag_redraw_headers():
    for area in bpy.context.screen.areas:
        if area.type in {'DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'NLA_EDITOR'}:
            area.tag_redraw()

def update_framerate_preset(scene):
    fps_real = scene.render.fps / scene.render.fps_base
    fps_real = round(fps_real, 2)

    preset_values = {
        23.98: '23.98',
        24.0: '24',
        25.0: '25',
        29.97: '29.97',
        30.0: '30',
        50.0: '50',
        59.94: '59.94',
        60.0: '60',
        120.0: '120',
        240.0: '240'
    }

    match = preset_values.get(fps_real)
    if match:
        scene.framerate_preset = match
    else:
        scene.framerate_preset = 'CUSTOM'
        scene.fr_target_fps = int(round(fps_real))
    tag_redraw_headers()

class FR_OT_SetFrameratePreset(bpy.types.Operator):
    bl_idname = "fr.set_framerate_preset"
    bl_label = "Set Framerate Preset"

    preset_value: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.framerate_preset = self.preset_value
        return {'FINISHED'}

classes = [
    FRAddonPreferences,
    FR_OT_Remap_Framerate,
    FR_PT_remap_in_output_format_like, 
    FR_MT_FramerateMenu,
    FR_OT_SetFrameratePreset
]

def register():
    bpy.app.timers.register(framerate_timer)

    for cls in classes:
        bpy.utils.register_class(cls)

    # プロパティ定義
    bpy.types.Scene.framerate_preset = bpy.props.EnumProperty(
        name="Framerate Preset",
        description="Choose a framerate preset",
        items=FRAMERATE_PRESETS,
        default='24'
    )
    bpy.types.Scene.fr_target_fps = bpy.props.IntProperty(
        name="Target FPS",
        description="Target framerate to remap",
        default=24,
        min=1,
        soft_max=240
    )

    # ヘッダーメニュー登録
    bpy.types.DOPESHEET_HT_header.append(dopesheet_menu)
    bpy.types.GRAPH_HT_header.append(graph_editor_menu)
    bpy.types.NLA_HT_header.append(nla_editor_menu)

def unregister():
    bpy.app.timers.unregister(framerate_timer)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.framerate_preset
    del bpy.types.Scene.fr_target_fps
    bpy.types.DOPESHEET_HT_header.remove(dopesheet_menu)
    bpy.types.GRAPH_HT_header.remove(graph_editor_menu)
    bpy.types.NLA_HT_header.remove(nla_editor_menu)

if __name__ == "__main__":
    register()
