#!/usr/bin/env python3
"""Check layout in desktop Qt 5, with original QRC parents and mocked NAC native types.

This is not Qt 5.5 on a NAC. No video decoder, physical display or vehicle input is tested.
"""
import argparse
import json
import os
import re
import tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_BACKEND','software')

from PyQt5.QtCore import QObject,pyqtSignal,pyqtProperty,QUrl,QT_VERSION_STR,PYQT_VERSION_STR,qVersion,qInstallMessageHandler
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlEngine,QQmlComponent,QQmlProperty
from audit_qrc import SPECS,resource
from patch_fullscreen_lab import patch_qml,read_file

STUBS={
'UiKit/BaseScreen.qml':'''import QtQuick 2.2
Item {
 property string context: ""
 property var showAnimation: null
 property var hideAnimation: null
 signal screenHideAnimationFinished()
 function startShowAnimation() {}
 function startCloseAnimation() {}
 function moveFocus(direction, animated) {}
 function activateCurrentFocusItem() {}
}''',
'UiKit/ScreenInfo.qml':'''pragma Singleton
import QtQml 2.2
QtObject {
 enum DisplayCategory { SD = 1, HD = 2, WHD = 3 }
 property int displayCategory: _labScreen.category
 property int width: _labScreen.width
 property int height: _labScreen.height
 function dpiPx(value) { return value; }
}''',
'UiKit/Style.qml':'''pragma Singleton
import QtQml 2.2
QtObject {
 property var prUniverseAmbiance: ({"font1": "Arial", "fontSize20": 20})
 property var ambiance: ({
 "global_content_background_color": "black", "primaryScreenBackgroundImageSource": "",
 "global_footer_background_color": "black", "fcb_footer_height": 100,
 "color_info": "white", "font1": "Arial", "fontSize20": 20
}) }''',
'UiKit/SystemCommands.qml':'''pragma Singleton
import QtQml 2.2
QtObject { property QtObject item: QtObject {} }''',
'UiKit/BackButton.qml':'''import QtQuick 2.2
Item { width: 86; height: 86; property bool showButtonBlackBackground: true; property bool pressed: false; signal clicked() }''',
'UiKit/VerticalSeparator.qml':'''import QtQuick 2.2
Item { width: 1; height: 1 }''',
'UiKit/FooterHeaderSeparator.qml':'''import QtQuick 2.2
Item { width: 1; height: 1 }''',
'UiKit/LayerWidget.qml':'''import QtQuick 2.2
Item { objectName: "LabLayerWidget"; property var layerMasks: []; anchors.fill: parent }''',
'UiKit/Label.qml':'''import QtQuick 2.2
Text {}''',
'AAutoApi/AAutoApi.qml':'''pragma Singleton
import QtQml 2.2
QtObject {
 property bool renderingHandled: _labScreen.rendering
 property bool firstUserExperienceEnabled: _labScreen.firstUse
}''',
}

class Inputs(QObject):
    changed=pyqtSignal()
    def __init__(self):super().__init__();self.w=1920;self.h=720;self.cat=3;self.video=True;self.first=False
    @pyqtProperty(int,notify=changed)
    def width(self):return self.w
    @pyqtProperty(int,notify=changed)
    def height(self):return self.h
    @pyqtProperty(int,notify=changed)
    def category(self):return self.cat
    @pyqtProperty(bool,notify=changed)
    def rendering(self):return self.video
    @pyqtProperty(bool,notify=changed)
    def firstUse(self):return self.first

class ScreenManagerStub(QObject):
    sgnFocusGained=pyqtSignal()
    sgnFocusLost=pyqtSignal()
    sgnShowing=pyqtSignal()
    sgnHiding=pyqtSignal()

_APPLICATION=None

def run_layout(rootfs,qml_file):
    global _APPLICATION
    if _APPLICATION is None:_APPLICATION=QGuiApplication.instance() or QGuiApplication([])
    app=_APPLICATION
    original=read_file(qml_file);candidate=patch_qml(original)
    with tempfile.TemporaryDirectory(prefix='nac-qml-lab-') as folder:
        folder=Path(folder)
        for name,text in STUBS.items():
            p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        core=resource((Path(rootfs)/SPECS[0]['file']).read_bytes(),SPECS[0])[0]
        full=resource((Path(rootfs)/SPECS[1]['file']).read_bytes(),SPECS[1])[0]
        (folder/'UiKit/Screen.qml').write_bytes(core)
        # The hidden footer uses a Continental attached type absent on the PC.
        # Remove only these three footer bindings in the desktop fixture, not in the candidate.
        full_desktop,count=re.subn(rb'^\s*Separator\.(?:linkSpacing|delegate|provideNeighbours):[^\n]*\n',b'\n',full,flags=re.M)
        if count!=3:raise ValueError('Unexpected footer adaptation count.')
        (folder/'UiKit/FullscreenContentScreen.qml').write_bytes(full_desktop)
        (folder/'UiKit/qmldir').write_text('module UiKit\n'+''.join(
            ('singleton ' if p.stem in ('ScreenInfo','Style','SystemCommands') else '')+p.stem+' 1.0 '+p.name+'\n'
            for p in sorted((folder/'UiKit').glob('*.qml'))))
        (folder/'AAutoApi/qmldir').write_text('module AAutoApi\nsingleton AAutoApi 1.0 AAutoApi.qml\n')
        (folder/'original.qml').write_bytes(original);(folder/'candidate.qml').write_bytes(candidate)
        inputs=Inputs();manager=ScreenManagerStub();identity=QObject()
        engine=QQmlEngine();engine.addImportPath(str(folder));ctx=engine.rootContext()
        ctx.setContextProperty('_labScreen',inputs);ctx.setContextProperty('screenManager',manager)
        ctx.setContextProperty('thisScreenID',identity)
        components=[];objects=[];messages=[]
        previous_handler=qInstallMessageHandler(lambda kind,ctx,message:messages.append(message.replace(str(folder),'<temporary>')))
        for name in ('original.qml','candidate.qml'):
            component=QQmlComponent(engine,QUrl.fromLocalFile(str(folder/name)))
            if component.isError():raise RuntimeError('\n'.join(e.toString() for e in component.errors()))
            obj=component.create()
            if obj is None:raise RuntimeError('\n'.join(e.toString() for e in component.errors()))
            components.append(component);objects.append(obj)
        rows=[]
        for w,h,cat,video,first in [
            (1920,720,3,True,False),(1280,720,2,True,False),(800,480,1,True,False),
            (1920,768,3,True,False),(2560,720,3,True,False),
            (1920,720,3,False,False),(1920,720,3,True,True),
        ]:
            inputs.w=w;inputs.h=h;inputs.cat=cat;inputs.video=video;inputs.first=first;inputs.changed.emit()
            app.processEvents();pair=[]
            for obj in objects:
                content=QQmlProperty.read(obj,'contentArea');mask=obj.findChild(QObject,'LabLayerWidget')
                # Use JS evaluation of the actual bound layerMasks variant, exposed through a QQmlExpression.
                from PyQt5.QtQml import QQmlExpression
                expression=QQmlExpression(engine.rootContext(),mask,'layerMasks.length ? layerMasks[0].width : -1')
                mask_width=expression.evaluate()[0]
                pair.append({'x':obj.property('x'),'width':obj.property('width'),'height':obj.property('height'),
                             'content_width':content.property('width'),'clip':content.property('clip'),
                             'mask_width':mask_width})
            rows.append({'screen':[w,h],'category':cat,'video':video,'first_use':first,
                         'original':pair[0],'candidate':pair[1]})
        from PyQt5 import sip
        for obj in objects:sip.delete(obj)
        sip.delete(engine)
        qInstallMessageHandler(previous_handler)
        errors=[m for m in messages if any(word in m for word in ('TypeError','ReferenceError','binding loop'))]
        if errors:raise RuntimeError('\n'.join(errors))
        result={'scope':'Desktop Qt layout only; BaseScreen, ScreenInfo, style, APIs, LayerWidget and manager are mocks.',
                'parent_sources_verified_before_desktop_adaptation':True,
                'desktop_only_adaptation':'Three attached Separator bindings removed from the hidden footer; original candidate does not change this resource.',
                'runtime_qt':qVersion(),
                'binding_build_qt':QT_VERSION_STR,'pyqt':PYQT_VERSION_STR,
                'desktop_warnings':messages,
                'nac_qt_5_5_executed':False,'video_rendering_or_touch_tested':False,'cases':rows}
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rootfs',required=True,type=Path);p.add_argument('--ui-file',required=True,type=Path);a=p.parse_args()
    print(json.dumps(run_layout(a.rootfs,a.ui_file),indent=2))

if __name__=='__main__':main()
