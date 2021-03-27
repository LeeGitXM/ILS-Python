'''
Code to be used in the configureChart extension function
for a jfreechart xy scatter plot

@author: phass
'''
import system
import org.jfree.chart.renderer.xy.AbstractXYItemRenderer as AbstractXYItemRenderer
import java.awt.Color as Color
import java.awt.geom.Rectangle2D as Rectangle2D
import java.awt.geom.Ellipse2D as Ellipse2D
import org.jfree.chart.plot.PlotOrientation as PlotOrientation
import org.jfree.util.ShapeUtilities as ShapeUtilities
from ils.jChart.common import getPlot
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)


# Configure the chart with a custom renderer that colors
# the points based on their place within the sequence.
def configure(chart, jChart, startColor, endColor, datasetIndex=0, shapeType="circle", size=2):
    log.infof("In %s.configure: dataset index: %d, color: (%d,%d,%d)->(%d,%d,%d)", __name__, datasetIndex, startColor.getRed(), startColor.getGreen(), startColor.getBlue(), endColor.getRed(), endColor.getGreen(), endColor.getBlue())
    renderer = colorRenderer(startColor,endColor, shapeType, size)
    plot = getPlot(jChart,0)
    plot.setRenderer(datasetIndex,renderer)

 
# Render scatterplot points with different colors for each
# point pased on its age - actually position in array.
class colorRenderer (AbstractXYItemRenderer):
     
    def __init__(self, startColor, endColor, shapeType, size):
        log.tracef("Initializing a new renderer!")
        self.startColor = startColor
        self.endColor = endColor
        if shapeType == "square":
            self.shapeType = "square"
        else:
            self.shapeType = "circle"
        if size < 1:
            self.size = 1
        elif size > 25:
            self.size = 25
        else:
            self.size = size
        
        if self.shapeType == "circle":
            self.setSeriesShape(0, Ellipse2D.Double(-0.5 * self.size, -0.5 * self.size, self.size, self.size))
        else:
            self.setSeriesShape(0, Rectangle2D.Double(-0.5 * self.size, -0.5 * self.size, self.size, self.size))
            
        print "Bar"
        log.tracef("start color: (%d, %d, %d, %d)", startColor.getRed(), startColor.getGreen(), startColor.getBlue(), startColor.getAlpha())
        log.tracef("end color: (%d, %d, %d, %d)", endColor.getRed(), endColor.getGreen(), endColor.getBlue(), endColor.getAlpha())
        
        
    # Overrite
    def drawItem(self, g2, state, dataArea, info, plot, domainAxis, rangeAxis, dataset,  series, item, crosshairState, success):
        shape = self.getItemShape(series,item)
        #shape =  Rectangle2D.Double(-5., -5., 10., 10.)
        
        x = dataset.getXValue(series, item)
        y = dataset.getYValue(series, item)
        transX = domainAxis.valueToJava2D(x, dataArea,plot.getDomainAxisEdge())
        transY = rangeAxis.valueToJava2D(y, dataArea,plot.getRangeAxisEdge())
        orientation = plot.getOrientation();
        if orientation == PlotOrientation.HORIZONTAL:
            shape = ShapeUtilities.createTranslatedShape(shape, transY,transX)
        elif orientation == PlotOrientation.VERTICAL:
            shape = ShapeUtilities.createTranslatedShape(shape, transX,transY)
        
#        count = plot.getDataset().getItemCount(series) - 1
        count = dataset.getItemCount(series) - 1
        if count<1: count = 1
        log.tracef("drawItem: (%f, %f) - %d of %d", x, y, int(item),int(count))
        
        color = self.interpolate(self.startColor, self.endColor, float(item)/count)
        log.tracef("   using interpolated color: (%d, %d, %d)", int(color.getRed()), int(color.getGreen()), int(color.getBlue()))
        g2.setPaint(color)
        g2.fill(shape)
        g2.draw(shape)
        

    # frac is (0.,1.]
    def interpolate(self, startColor, endColor, frac):
        red   = startColor.getRed()*frac   + endColor.getRed()*(1.-frac)
        green = startColor.getGreen()*frac + endColor.getGreen()*(1.-frac)
        blue  = startColor.getBlue()*frac  + endColor.getBlue()*(1.-frac)
        alpha = startColor.getAlpha()*frac + endColor.getAlpha()*(1.-frac)
        
        red   = endColor.getRed()*frac   + startColor.getRed()*(1.-frac)
        green = endColor.getGreen()*frac + startColor.getGreen()*(1.-frac)
        blue  = endColor.getBlue()*frac  + startColor.getBlue()*(1.-frac)
        alpha = endColor.getAlpha()*frac + startColor.getAlpha()*(1.-frac)
        
        # Args are float values in the range (0,1)
        return Color(red/255., green/255., blue/255., alpha/255.)      