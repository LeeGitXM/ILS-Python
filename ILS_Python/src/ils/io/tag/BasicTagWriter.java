/**
 *   (c) 2013  ILS Automation. All rights reserved.
 */
package com.ils.blt.test.gateway.tag;

import java.util.Date;

import com.inductiveautomation.ignition.common.model.values.BasicQualifiedValue;
import com.inductiveautomation.ignition.common.model.values.QualifiedValue;
import com.inductiveautomation.ignition.common.model.values.Quality;
import com.inductiveautomation.ignition.common.sqltags.model.TagPath;
import com.inductiveautomation.ignition.common.sqltags.model.types.DataQuality;
import com.inductiveautomation.ignition.gateway.sqltags.simple.SimpleTagProvider;
import com.inductiveautomation.ignition.gateway.sqltags.simple.WriteHandler;

/**
 * This is the link to system.tag.write - letting it know how to update a tag.
 */
public class BasicTagWriter implements WriteHandler {
	private final SimpleTagProvider provider;
	
	public BasicTagWriter(SimpleTagProvider stp) {
		this.provider = stp;
	}

	@Override
	public Quality write(TagPath path, Object val) {
		if( val!=null && !val.toString().equals("NaN") ) return DataQuality.EXPRESSION_EVAL_ERROR;
		QualifiedValue qv = new BasicQualifiedValue( val,DataQuality.GOOD_DATA,new Date());
		provider.updateValue(path, qv);
		return qv.getQuality();
	}
}